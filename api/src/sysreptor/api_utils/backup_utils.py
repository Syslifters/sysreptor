import contextlib
import io
import itertools
import json
import logging
import os
import zipfile
from pathlib import Path

import boto3
import zipstream
from django.apps import apps
from django.conf import settings
from django.core import serializers
from django.core.management import call_command
from django.core.management.color import no_style
from django.core.serializers.base import DeserializationError
from django.core.serializers.json import DjangoJSONEncoder
from django.core.serializers.jsonl import Deserializer as JsonlDeserializer
from django.db import connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.loader import MigrationLoader

from sysreptor.api_utils.models import BackupLog, BackupLogType
from sysreptor.pentests import storages
from sysreptor.pentests.models import (
    ArchivedProject,
    UploadedAsset,
    UploadedImage,
    UploadedProjectFile,
    UploadedTemplateImage,
    UploadedUserNotebookFile,
    UploadedUserNotebookImage,
)
from sysreptor.pentests.models.project import ProjectMemberRole
from sysreptor.utils import crypto
from sysreptor.utils.configuration import configuration


class DbJsonlDeserializer(JsonlDeserializer):
    def __init__(self, *args, migration_apps=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.migration_apps = migration_apps or apps

    def _get_model_from_node(self, model_identifier):
        app_label, model_name = model_identifier.split('.')
        try:
            return self.migration_apps.get_model(app_label, model_name)
        except LookupError as ex:
            if app_label.startswith('plugin_'):
                raise DeserializationError(f'Plugin model "{model_identifier}" not found. Plugin is probably not enabled.') from ex
            else:
                raise ex


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


def create_configurations_backup():
    out = {
        'format': 'configurations/v1',
        'configurations': [],
    }
    for f in configuration.definition.fields:
        if not f.extra_info.get('internal'):
            out['configurations'].append({
                'name': f.id,
                'value': configuration.get(f.id),
            })
    return out


def create_database_dump():
    """
    Return a database dump of django models. It uses the same format as "manage.py dumpdata --format=jsonl".
    """
    exclude_models = ['contenttypes.ContentType', 'sessions.Session', 'users.Session', 'admin.LogEntry', 'auth.Permission', 'auth.Group',
                      'pentests.LockInfo', 'pentests.CollabEvent', 'pentests.CollabClientInfo', 'api_utils.DbConfigurationEntry']
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
                            use_natural_primary_keys=False,
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


def create_backup(user=None):
    logging.info('Backup requested')

    z = zipstream.ZipStream(compress_type=zipstream.ZIP_DEFLATED)
    z.add(arcname='VERSION', data=settings.VERSION.encode())
    z.add(arcname='migrations.json', data=json.dumps(create_migration_info()).encode())
    z.add(arcname='configurations.json', data=json.dumps(create_configurations_backup()).encode())
    z.add(arcname='backup.jsonl', data=create_database_dump())

    backup_files(z, 'uploadedimages', storages.get_uploaded_image_storage(), [UploadedImage, UploadedUserNotebookImage, UploadedTemplateImage])
    backup_files(z, 'uploadedassets', storages.get_uploaded_asset_storage(), [UploadedAsset])
    backup_files(z, 'uploadedfiles', storages.get_uploaded_file_storage(), [UploadedProjectFile, UploadedUserNotebookFile])
    backup_files(z, 'archivedfiles', storages.get_archive_file_storage(), [ArchivedProject])

    BackupLog.objects.create(type=BackupLogType.BACKUP, user=user)

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


def to_chunks(z, allow_small_first_chunk=False):
    buffer = bytearray()
    is_first_chunk = True

    for chunk in z:
        buffer.extend(chunk)
        while len(buffer) > settings.FILE_UPLOAD_MAX_MEMORY_SIZE or (is_first_chunk and allow_small_first_chunk):
            yield bytes(buffer[:settings.FILE_UPLOAD_MAX_MEMORY_SIZE])
            del buffer[:settings.FILE_UPLOAD_MAX_MEMORY_SIZE]
            is_first_chunk = False

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
    tables = connection.introspection.table_names(include_views=False)
    views = set(connection.introspection.table_names(include_views=True)) - set(tables)
    connection.check_constraints()
    with connection.cursor() as cursor:
        cursor.execute(
            'DROP TABLE IF EXISTS ' +
            ', '.join([connection.ops.quote_name(t) for t in tables]) +
            ' CASCADE;',
        )
        cursor.execute(
            'DROP VIEW IF EXISTS ' +
            ', '.join([connection.ops.quote_name(v) for v in views]) +
            ' CASCADE;',
        )


def restore_database_dump(f):
    """
    Import DB dump from JSONL file line by line.
    By default django serializers use the current model state from code, not at the time of the backup to restore.
    When DB models change, we would not be able to fully restore all fields.
    Therefore, we patch the django serializer to use the model at the current migration state, not the model from code.
    """
    migration_apps = MigrationExecutor(connection)._create_project_state(with_applied_migrations=True).apps

    # Defer DB constraint checking
    with constraint_checks_disabled():
        objs_with_deferred_fields = []
        for obj in DbJsonlDeserializer(f, migration_apps=migration_apps, handle_forward_references=True, ignorenonexistent=True):
            obj.save()
            if obj.deferred_fields:
                objs_with_deferred_fields.append(obj)
        for obj in objs_with_deferred_fields:
            obj.save_deferred_fields()

    # Check DB constraints
    connection.check_constraints()


def reset_database_sequences():
    app_list = [app_config for app_config in apps.get_app_configs() if app_config.models_module is not None]
    models = list(itertools.chain(*map(lambda a: a.get_models(include_auto_created=True), app_list)))
    statements = connection.ops.sequence_reset_sql(style=no_style(), model_list=models)
    with connection.cursor() as cursor:
        cursor.execute('\n'.join(statements))


def walk_storage_dir(storage, base_dir=None):
    base_dir = base_dir or ''
    try:
        dirs, files = storage.listdir(base_dir)
    except FileNotFoundError:
        return
    except Exception as ex:
        raise Exception(f'Could not do listdir with base_dir "{base_dir}" and storage location "{storage.location}"') from ex
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


def restore_configurations(z):
    configurations_file = zipfile.Path(z, 'configurations.json')
    if not configurations_file.exists():
        logging.info('No saved configurations in backup')
        return

    configurations_data = json.loads(configurations_file.read_text())
    if isinstance(configurations_data, dict) and configurations_data.get('format') == 'configurations/v1':
        configuration.update({c['name']: c['value'] for c in configurations_data.get('configurations', [])}, only_changed=False)
    else:
        logging.warning('Unknown format in configurations.json')


@transaction.atomic
def restore_backup(z, keepfiles=True, skip_files=False, skip_database=False):
    logging.info('Begin restoring backup')

    backup_version_file = zipfile.Path(z, 'VERSION')
    if backup_version_file.exists():
        version = backup_version_file.read_text()
        if version != settings.VERSION or version == 'dev' or settings.VERSION == 'dev':
            logging.warning(f'Restoring backup generated by SysReptor version {version} to SysReptor version {settings.VERSION}.')
    else:
        logging.warning('No version information found in backup file.')

    if not skip_database:
        # Load migrations
        migrations = None
        configurations_file = zipfile.Path(z, 'migrations.json')
        if configurations_file.exists():
            migrations_info = json.loads(configurations_file.read_text())
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
                if m['app_label'].startswith('plugin_') and not any(a for a in apps.get_app_configs() if a.label == m['app_label']):
                    logging.warning(f'Cannot run migation "{m["migration_name"]}", because plugin "{m["app_label"]}" is not enabled. Plugin data will not be restored.')
                    continue

                call_command('migrate', app_label=m['app_label'], migration_name=m['migration_name'], interactive=False, verbosity=0)
        else:
            logging.warning('No migrations info found in backup. Applying all available migrations')
            call_command('migrate', interactive=False, verbosity=0)
        logging.info('Finished migrations')

        # Delete data created in migrations
        ProjectMemberRole.objects.all().delete()
        BackupLog.objects.all().delete()

        # Restore DB data
        logging.info('Begin restoring DB data')
        with z.open('backup.jsonl') as f:
            restore_database_dump(f)
        logging.info('Finished restoring DB data')

        # Reset sequences
        logging.info('Begin resetting DB sequences')
        reset_database_sequences()
        logging.info('Finished resetting DB sequences')

    if not skip_files:
        # Restore files
        logging.info('Begin restoring files')
        if not keepfiles:
            delete_all_storage_files()
        restore_files(z)
        logging.info('Finished restoring files')

    if not skip_database:
        # Apply remaining migrations
        logging.info('Begin running new migrations')
        with constraint_checks_immediate():
            call_command('migrate', interactive=False, verbosity=0)
        logging.info('Finished running new migrations')

        # Restore configurations
        logging.info('Begin restoring configurations')
        restore_configurations(z)
        logging.info('Finished restoring configurations')

    logging.info('Finished backup restore')
    BackupLog.objects.create(type=BackupLogType.RESTORE, user=None)

