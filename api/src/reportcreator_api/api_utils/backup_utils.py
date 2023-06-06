import logging
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

from reportcreator_api.archive import crypto
from reportcreator_api.pentests.models import UploadedImage, UploadedAsset, UploadedProjectFile, UploadedUserNotebookImage, ArchivedProject


def create_database_dump():
    """
    Return a database dump of django models. It uses the same format as "manage.py dumpdata --format=jsonl".
    """
    exclude_models = ['contenttypes.ContentType', 'sessions.Session', 'users.Session', 'admin.LogEntry', 'auth.Permission', 'auth.Group', 'pentests.LockInfo']
    try:
        app_list = [app_config for app_config in apps.get_app_configs() if app_config.models_module is not None]
        models = list(itertools.chain(*map(lambda a: a.get_models(), app_list)))
        for model in models:
            natural_key = True
            if model._meta.label == 'users.PentestUser':
                natural_key = False
            if model._meta.label not in exclude_models:
                for e in model._default_manager.order_by(model._meta.pk.name).iterator():
                    yield json.dumps(
                        serializers.serialize(
                            'python', 
                            [e], 
                            use_natural_foreign_keys=natural_key,
                            use_natural_primary_keys=natural_key
                        )[0], cls=DjangoJSONEncoder, ensure_ascii=True).encode() + b'\n'
    except Exception as ex:
        logging.exception('Error creating database dump')
        raise ex


def backup_files(z, model, path):
    def file_chunks(f):
        try:
            yield from model.file.field.storage.open(f).chunks()
        except (FileNotFoundError, OSError) as ex:
            logging.warning(f'Could not backup file {f}: {ex}')

    for f in model.objects.values_list('file', flat=True).distinct().iterator():
        z.write_iter(str(Path(path) / f), file_chunks(f))


def create_backup():
    logging.info('Backup requested')
    z = zipstream.ZipFile(mode='w', compression=zipstream.ZIP_DEFLATED, allowZip64=True)
    z.writestr('VERSION', settings.VERSION.encode())
    z.write_iter('backup.jsonl', create_database_dump())

    backup_files(z, UploadedImage, 'uploadedimages')
    backup_files(z, UploadedUserNotebookImage, 'uploadedimages')
    backup_files(z, UploadedAsset, 'uploadedassets')
    backup_files(z, UploadedProjectFile, 'uploadedfiles')
    backup_files(z, ArchivedProject, 'archivedfiles')
    
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
