import concurrent.futures
import contextlib
import gc
import io
import itertools
import json
import logging
import os
import zipfile
from collections import deque
from pathlib import Path
from queue import Empty, Full, Queue
from threading import Event

import zipstream
from django.apps import apps
from django.conf import settings
from django.core import serializers
from django.core.files.storage import storages
from django.core.management import call_command
from django.core.management.color import no_style
from django.core.serializers.base import DeserializationError
from django.core.serializers.json import DjangoJSONEncoder
from django.core.serializers.jsonl import Deserializer as JsonlDeserializer
from django.db import connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.loader import MigrationLoader
from django.utils import timezone

from sysreptor.api_utils.models import BackupLog, BackupLogType, DbConfigurationEntry
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
                      'pentests.LockInfo', 'pentests.CollabEvent', 'pentests.CollabClientInfo', 'pentests.BlindTrigramToken',
                      'api_utils.DbConfigurationEntry']
    try:
        app_list = [app_config for app_config in apps.get_app_configs() if app_config.models_module is not None]
        models = list(itertools.chain(*map(lambda a: a.get_models(), app_list)))
        for model in models:
            if model._meta.label in exclude_models:
                continue

            qs = model._default_manager.order_by(model._meta.pk.name)
            m2m_field_names = [
                f.name for f in model._meta.local_many_to_many
                if f.serialize and f.remote_field.through._meta.auto_created
            ]
            if m2m_field_names:
                qs = qs.prefetch_related(*m2m_field_names)

            for e in qs.iterator(chunk_size=2000):
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


def get_storage_dirs():
    return {k: storages[k] for k in storages.backends.keys() if k not in ['staticfiles', 'default']}


class ChunkPipe:
    _SENTINEL = object()

    def __init__(self, *, max_queue_items: int = 5) -> None:
        self.queue: Queue = Queue(maxsize=max(1, int(max_queue_items)))
        self.cancelled = Event()

    def push(self, data) -> None:
        while True:
            if self.cancelled.is_set():
                return
            try:
                self.queue.put(data, timeout=1)
                return
            except Full:
                pass
            except Exception:
                self.cancelled.set()
                raise

    def fail(self, ex) -> None:
        self.push(ex)

    def close(self) -> None:
        self.push(self._SENTINEL)

    def cancel(self) -> None:
        self.cancelled.set()
        # Drain any queued chunks.
        while True:
            try:
                item = self.queue.get_nowait()
            except Empty:
                return
            if item is self._SENTINEL:
                return

    def iter_items(self):
        try:
            while True:
                item = self.queue.get()
                if item is self._SENTINEL:
                    return
                elif isinstance(item, Exception):
                    raise item
                yield item
        finally:
            self.cancel()


class BackupFilePrefetcher:
    def __init__(
        self,
        *,
        executor: concurrent.futures.ThreadPoolExecutor,
        storage,
        files: list[str],
        prefetch_size: int = 10,
        chunk_size: int | None = None,
        backup_stats: dict | None = None,
    ) -> None:
        self.executor = executor
        self.storage = storage
        self.files = list(files)
        self.prefetch_size = max(1, int(prefetch_size))
        self.chunk_size = chunk_size or settings.FILE_UPLOAD_MAX_MEMORY_SIZE
        self.backup_stats = backup_stats
        self._in_flight: deque[tuple[str, ChunkPipe]] = deque()
        self._next_submit_idx = 0

    def _produce_chunks(self, name: str, pipe: ChunkPipe) -> None:
        try:
            with self.storage.open(name) as fp:
                for chunk in fp.chunks(chunk_size=self.chunk_size):
                    if pipe.cancelled.is_set():
                        break
                    pipe.push(chunk)
        except Exception as ex:
            pipe.fail(ex)
        finally:
            pipe.close()

    def _submit_next(self) -> bool:
        if self._next_submit_idx >= len(self.files):
            return False
        f = self.files[self._next_submit_idx]
        self._next_submit_idx += 1

        pipe = ChunkPipe()
        self.executor.submit(self._produce_chunks, f, pipe)
        self._in_flight.append((f, pipe))
        return True

    def _ensure_in_flight(self) -> None:
        while len(self._in_flight) < self.prefetch_size and self._submit_next():
            pass

    def _file_chunks(self, name: str):
        # Maintain the rolling prefetch window lazily, when the zipstream consumer
        # actually starts pulling chunks for this entry. This keeps iter_entries
        # non-blocking and ensures prefetching happens during streaming.
        self._ensure_in_flight()
        if not self._in_flight:
            return

        actual_name, pipe = self._in_flight.popleft()
        if actual_name != name:
            raise RuntimeError('Backup prefetch queue out of sync')

        try:
            yield from pipe.iter_items()
            if self.backup_stats is not None:
                self.backup_stats['file_successes'] = self.backup_stats.get('file_successes', 0) + 1
        except (FileNotFoundError, OSError):
            if self.backup_stats is not None:
                self.backup_stats['file_errors'] = self.backup_stats.get('file_errors', 0) + 1
        finally:
            pipe.cancel()

    def iter_entries(self):
        for f in self.files:
            yield f, self._file_chunks(f)

    def cancel(self) -> None:
        while self._in_flight:
            _, pipe = self._in_flight.popleft()
            pipe.cancel()


def backup_files(z, path, storage, executor, backup_stats=None):
    prefetcher = BackupFilePrefetcher(
        executor=executor,
        storage=storage,
        files=walk_storage_dir(storage),
        prefetch_size=settings.BACKUP_FILE_PREFETCH_SIZE,
        backup_stats=backup_stats,
    )

    original_compress_level = z._compress_level
    original_compress_type = z._compress_type
    if path in ['uploadedimages', 'archivedfiles']:
        # Do not compress images because most image file formats are already compressed.
        # Archived files are compressed and encrypted
        z._compress_level = None
        z._compress_type = zipstream.ZIP_STORED

    for f, data_iter in prefetcher.iter_entries():
        z.add(arcname=str(Path(path) / f), data=data_iter)

    z._compress_level = original_compress_level
    z._compress_type = original_compress_type

    return prefetcher


def create_backup(user=None):
    logging.info('Backup requested')
    backup_log_started = BackupLog.objects.create(type=BackupLogType.BACKUP_STARTED, user=user)

    z = zipstream.ZipStream(compress_type=zipstream.ZIP_DEFLATED, compress_level=3)
    z.add(arcname='VERSION', data=settings.VERSION.encode())
    z.add(arcname='migrations.json', data=json.dumps(create_migration_info()).encode())
    z.add(arcname='configurations.json', data=json.dumps(create_configurations_backup()).encode())
    z.add(arcname='backup.jsonl', data=create_database_dump())

    executor = concurrent.futures.ThreadPoolExecutor(
        max_workers=settings.BACKUP_FILE_PREFETCH_WORKERS,
        thread_name_prefix='backup-prefetch',
    )
    backup_stats = {}
    prefetchers: list[BackupFilePrefetcher] = []
    for d, storage in get_storage_dirs().items():
        prefetchers.append(backup_files(z, d, storage, executor=executor, backup_stats=backup_stats))

    def get_backup_stats():
        yield b''
        finished = timezone.now()
        yield json.dumps({
            'started': backup_log_started.created.isoformat(),
            'finished': finished.isoformat(),
        }).encode()

        if backup_stats.get('file_errors', 0) > 0:
            logging.warning(f'Could not backup {backup_stats.get("file_errors", 0)} / {backup_stats.get("file_errors", 0) + backup_stats.get("file_successes", 0)} files.')

        BackupLog.objects.create(type=BackupLogType.BACKUP_FINISHED, user=user, created=finished)
        logging.info('Backup finished')
        gc.collect()
    z.add(arcname='stats.json', data=get_backup_stats())

    def stream():
        try:
            yield from z
        finally:
            for p in prefetchers:
                p.cancel()
            executor.shutdown(wait=True)
    return stream()


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
    import boto3
    logging.info('Uploading backup to S3 bucket')
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
        batch = []
        for obj in DbJsonlDeserializer(f, migration_apps=migration_apps, handle_forward_references=True, ignorenonexistent=True):
            if batch and (len(batch) == 1000 or batch[0].__class__ != obj.object.__class__):
                batch[0].__class__.objects.bulk_create(batch)
                batch.clear()

            if not obj.m2m_data:
                # Bulk insert if possible
                batch.append(obj.object)
            else:
                obj.save()

            if obj.deferred_fields:
                objs_with_deferred_fields.append(obj)
        if batch:
            batch[0].__class__.objects.bulk_create(batch)
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
    for storage in get_storage_dirs().values():
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
    for d, storage in get_storage_dirs().items():
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
        migration_loader = MigrationLoader(connection)
        if migrations is not None:
            for m in migrations:
                if not any(a for a in apps.get_app_configs() if a.label == m['app_label']):
                    if m['app_label'].startswith('plugin_'):
                        logging.warning(f'Cannot run migation "{m["migration_name"]}", because plugin "{m["app_label"]}" is not enabled. Plugin data will not be restored.')
                    else:
                        logging.warning(f'Cannot run migation "{m["migration_name"]}", because app "{m["app_label"]}" is not installed. Skipping')
                    continue

                try:
                    migration_loader.get_migration(m['app_label'], m['migration_name'])
                except KeyError:
                    logging.warning(f'Cannot find migration "{m["migration_name"]}" for app "{m["app_label"]}". Skipping')
                    continue

                call_command('migrate', app_label=m['app_label'], migration_name=m['migration_name'], interactive=False, verbosity=0)
        else:
            logging.warning('No migrations info found in backup. Applying all available migrations')
            call_command('migrate', interactive=False, verbosity=0)
        logging.info('Finished migrations')

        # Delete data created in migrations
        ProjectMemberRole.objects.all().delete()
        BackupLog.objects.all().delete()
        DbConfigurationEntry.objects.all().delete()

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

