import subprocess
import logging
import zipstream
import boto3
from pathlib import Path

from reportcreator_api.pentests.models import UploadedImage, UploadedAsset


def create_database_dump():

    """dbuser = settings.DATABASES['default']['USER']
    dbpass = settings.DATABASES['default']['PASSWORD']
    dbname = settings.DATABASES['default']['NAME']
    dbhost = settings.DATABASES['default']['HOST']
    dbport = settings.DATABASES['default']['PORT']
    # test if pg_dump is installed
    try:
        subprocess.run(['pg_dump', '--version'], check=True)
    except subprocess.CalledProcessError:
        raise Exception('pg_dump not installed')


    proc = subprocess.Popen(['pg_dump', '-U', dbuser, '-h', dbhost, '-p', dbport, '-d', dbname], stdout=subprocess.PIPE,
                            env={'PGPASSWORD': dbpass})"""

    proc = subprocess.Popen(['python', 'manage.py', 'dumpdata'], stdout=subprocess.PIPE)
    for c in iter(lambda: proc.stdout.read(1024), b""):
        yield c


def backup_files(z, model, path):
    for f in model.objects.values_list('file', flat=True).distinct().iterator():
        z.write_iter(str(Path(path) / f), model.file.field.storage.open(f).chunks())


def create_backup():
    logging.info('Backup requested')
    z = zipstream.ZipFile(mode='w', compression=zipstream.ZIP_DEFLATED)
    z.write_iter('backup.json', create_database_dump())

    backup_files(z, UploadedImage, 'uploadedimages')
    backup_files(z, UploadedAsset, 'uploadedassets')
    
    return z


def upload_to_s3_bucket(z, s3_params):
    s3 = boto3.resource('s3', **s3_params.get('boto3_params', {}))
    bucket = s3.Bucket(s3_params['bucket_name'])

    class Wrapper:
        def __init__(self, z):
            self.z = z
            self.buffer = b''
            self.iter = z.__iter__()

        def read(self, size=8192):
            while len(self.buffer) < size:
                try:
                    self.buffer += next(self.iter)
                except StopIteration:
                    break
            ret = self.buffer[:size]

            self.buffer = self.buffer[size:]
            return ret

    bucket.upload_fileobj(Wrapper(z), s3_params['key'])

