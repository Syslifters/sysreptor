import contextlib
import logging
import os
from unittest import mock
import zipfile
import zipstream
import boto3
import io
import json
import itertools
from pathlib import Path
from django.conf import settings
from django.apps import apps
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.core.management import call_command
from django.db import connection, transaction
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.recorder import MigrationRecorder
from django.db.migrations.executor import MigrationExecutor

from reportcreator_api.archive import crypto
from reportcreator_api.pentests.models import UploadedImage, UploadedAsset, UploadedProjectFile, ArchivedProject, \
    UploadedUserNotebookFile, UploadedUserNotebookImage, UploadedTemplateImage
from reportcreator_api.pentests import storages
from reportcreator_api.pentests.models.project import ProjectMemberRole


def create_migration_info():
    out = {
        'format': 'migrations/v1',
        'current': [],
        'all': [],
    }

    loader = MigrationLoader(connection)
    graph = loader.graph
    seen = set()
    for node in graph.leaf_nodes():
        out['current'].append({
            'app_label': node[0],
            'migration_name': node[1],
        })

        for dep_key in graph.forwards_plan(node):
            if dep_key not in seen:
                seen.add(dep_key)
                out['all'].append({
                    'app_label': dep_key[0],
                    'migration_name': dep_key[1],
                    'applied': dep_key in loader.applied_migrations,
                })
    return out


def create_database_dump():
    """
    Return a database dump of django models. It uses the same format as "manage.py dumpdata --format=jsonl".
    """
    exclude_models = ['contenttypes.ContentType', 'sessions.Session', 'users.Session', 'admin.LogEntry', 'auth.Permission', 'auth.Group', 
                      'pentests.LockInfo', 'pentests.CollabEvent']
    try:
        app_list = [app_config for app_config in apps.get_app_configs() if app_config.models_module is not None]
        models = list(itertools.chain(*map(lambda a: a.get_models(), app_list)))
        for model in models:
            if model._meta.label not in exclude_models:
                for e in model._default_manager.order_by(model._meta.pk.name).iterator():
                    yield json.dumps(
                        serializers.serialize(
                            'python', 
                            [e], 
                            use_natural_foreign_keys=False,
                            use_natural_primary_keys=False
                        )[0], cls=DjangoJSONEncoder, ensure_ascii=True).encode() + b'\n'
    except Exception as ex:
        logging.exception('Error creating database dump')
        raise ex


def backup_files(z, path, storage, models):
    def file_chunks(f):
        try:
            with storage.open(f) as fp:
                yield from fp.chunks()
        except (FileNotFoundError, OSError) as ex:
            logging.warning(f'Could not backup file {f}: {ex}')

    for m in list(models):
        if hasattr(m, 'history'):
            models.append(m.history.model)

    qs = models[0].objects.values_list('file', flat=True)
    if len(models) > 1:
        qs = qs.union(*[m.objects.values_list('file', flat=True) for m in models[1:]], all=False)
    else:
        qs = qs.distinct()
    for f in qs.iterator():
        z.add(arcname=str(Path(path) / f), data=file_chunks(f))


def create_backup():
    logging.info('Backup requested')
    z = zipstream.ZipStream(compress_type=zipstream.ZIP_DEFLATED)
    z.add(arcname='VERSION', data=settings.VERSION.encode())
    z.add(arcname='migrations.json', data=json.dumps(create_migration_info()).encode())
    z.add(arcname='backup.jsonl', data=create_database_dump())

    backup_files(z, 'uploadedimages', storages.get_uploaded_image_storage(), [UploadedImage, UploadedUserNotebookImage, UploadedTemplateImage])
    backup_files(z, 'uploadedassets', storages.get_uploaded_asset_storage(), [UploadedAsset])
    backup_files(z, 'uploadedfiles', storages.get_uploaded_file_storage(), [UploadedProjectFile, UploadedUserNotebookFile])
    backup_files(z, 'archivedfiles', storages.get_archive_file_storage(), [ArchivedProject])
    
    return z


def encrypt_backup(z, aes_key):
    buf = io.BytesIO()
    with crypto.open(fileobj=buf, mode='wb', key_id=None, key=crypto.EncryptionKey(id=None, key=aes_key)) as c:
        for chunk in z:
            c.write(chunk)
            yield buf.getvalue()
            buf.seek(0)
            buf.truncate()
    if remaining := buf.getvalue():
        yield remaining


def upload_to_s3_bucket(z, s3_params):
    s3 = boto3.resource('s3', **s3_params.get('boto3_params', {}))
    bucket = s3.Bucket(s3_params['bucket_name'])

    class Wrapper:
        def __init__(self, z):
            self.z = iter(z)
            self.buffer = b''

        def read(self, size=8192):
            while len(self.buffer) < size:
                try:
                    self.buffer += next(self.z)
                except StopIteration:
                    break
            ret = self.buffer[:size]

            self.buffer = self.buffer[size:]
            return ret

    bucket.upload_fileobj(Wrapper(z), s3_params['key'])


def to_chunks(z):
    buffer = bytearray()

    for chunk in z:
        buffer.extend(chunk)
        while len(buffer) > settings.FILE_UPLOAD_MAX_MEMORY_SIZE:
            yield bytes(buffer[:settings.FILE_UPLOAD_MAX_MEMORY_SIZE])
            del buffer[:settings.FILE_UPLOAD_MAX_MEMORY_SIZE]
    
    yield bytes(buffer)


@contextlib.contextmanager
def constraint_checks_disabled():
    with transaction.atomic(), connection.cursor() as cursor:
        try:
            cursor.execute("SET CONSTRAINTS ALL DEFERRED")
            yield
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        finally:
            cursor.execute("SET CONSTRAINTS ALL DEFERRED")


@contextlib.contextmanager
def constraint_checks_immediate():
    with connection.cursor() as cursor:
        try:
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
            yield
        finally:
            cursor.execute("SET CONSTRAINTS ALL DEFERRED")


def destroy_database():
    """
    Delete all DB data; drop all tables, views, sequences
    """
    tables = connection.introspection.django_table_names(include_views=True) + [MigrationRecorder.Migration._meta.db_table]
    connection.check_constraints()
    with connection.cursor() as cursor:
        cursor.execute(
            'DROP TABLE IF EXISTS ' + 
            ', '.join([connection.ops.quote_name(t) for t in tables]) + 
            ' CASCADE;'
        )


def restore_database_dump(f):
    """
    Import DB dump from JSONL file line by line.
    By default django serializers use the current model state from code, not at the time of the backup to restore.
    When DB models change, we would not be able to fully restore all fields.
    Therefore, we patch the django serializer to use the model at the current migration state, not the model from code.
    """
    migration_apps = MigrationExecutor(connection)._create_project_state(with_applied_migrations=True).apps
    def get_model(model_identifier):
        app_label, model_name = model_identifier.split('.')
        return migration_apps.get_model(app_label, model_name)

    # Defer DB constraint checking
    with constraint_checks_disabled(), \
        mock.patch('django.core.serializers.python._get_model', get_model):
        objs_with_deferred_fields = []
        for obj in serializers.deserialize('jsonl', f, handle_forward_references=True):
            obj.save()
            if obj.deferred_fields:
                objs_with_deferred_fields.append(obj)
        for obj in objs_with_deferred_fields:
            obj.save_deferred_fields()
    
    # Check DB constraints
    connection.check_constraints()


def walk_storage_dir(storage, base_dir=None):
    base_dir = base_dir or ''
    try:
        dirs, files = storage.listdir(base_dir)
    except FileNotFoundError:
        return
    for f in files:
        yield os.path.join(base_dir, f)
    for d in dirs:
        yield from walk_storage_dir(storage, os.path.join(base_dir, d))


def delete_all_storage_files():
    """
    Delete all files from storages
    """
    storage_list = [
        storages.get_uploaded_image_storage(), 
        storages.get_uploaded_asset_storage(), 
        storages.get_uploaded_file_storage(), 
        storages.get_archive_file_storage(),
    ]
    for storage in storage_list:
        for f in walk_storage_dir(storage):
            try:
                storage.delete(f)
            except OSError as ex:
                logging.warning(f'Could not delete file from storage: {ex}')


def walk_zip_dir(d):
    for f in d.iterdir():
        if f.is_file():
            yield f
        elif f.is_dir():
            yield from walk_zip_dir(f)


def restore_files(z):
    storage_dirs = {
        'uploadedimages': storages.get_uploaded_image_storage(), 
        'uploadedassets': storages.get_uploaded_asset_storage(), 
        'uploadedfiles': storages.get_uploaded_file_storage(), 
        'archivedfiles': storages.get_archive_file_storage(),
    }
    for d, storage in storage_dirs.items():
        d = zipfile.Path(z, d + '/')
        if d.exists() and d.is_dir():
            for f in walk_zip_dir(d):
                with f.open('rb') as fp:
                    storage.save(name=f.at[len(d.at):], content=fp)


@transaction.atomic
def restore_backup(z, keepfiles=True):
    logging.info('Begin restoring backup')

    backup_version_file = zipfile.Path(z, 'VERSION')
    if backup_version_file.exists():
        version = backup_version_file.read_text()
        if version != settings.VERSION or version == 'dev' or settings.VERSION == 'dev':
            logging.warning(f'Restoring backup generated by SysReptor version {version} to SysReptor version {version}.')
    else:
        logging.warning('No version information found in backup file.')

    # Load migrations
    migrations = None
    migrations_file = zipfile.Path(z, 'migrations.json')
    if migrations_file.exists():
        migrations_info = json.loads(migrations_file.read_text())
        assert migrations_info.get('format') == 'migrations/v1'
        migrations = migrations_info.get('current', [])
    
    # Delete all DB data
    logging.info('Begin destroying DB. Dropping all tables.')
    destroy_database()
    logging.info('Finished destroying DB')

    # Apply migrations from backup
    logging.info('Begin running migrations from backup')
    if migrations is not None:
        for m in migrations:
            call_command('migrate', app_label=m['app_label'], migration_name=m['migration_name'], interactive=False, verbosity=0)
    else:
        logging.warning('No migrations info found in backup. Applying all available migrations')
        call_command('migrate', interactive=False, verbosity=0)
    logging.info('Finished migrations')

    # Delete data created in migrations
    ProjectMemberRole.objects.all().delete()

    # Restore DB data
    logging.info('Begin restoring DB data')
    with z.open('backup.jsonl') as f:
        restore_database_dump(f)
    logging.info('Finished restoring DB data')
    
    # Restore files
    logging.info('Begin restoring files')
    if not keepfiles:
        delete_all_storage_files()
    restore_files(z)
    logging.info('Finished restoring files')
    
    # Apply remaining migrations
    logging.info('Begin running new migrations')
    with constraint_checks_immediate():
        call_command('migrate', interactive=False, verbosity=0)
    logging.info('Finished running new migrations')

    logging.info('Finished backup restore')


