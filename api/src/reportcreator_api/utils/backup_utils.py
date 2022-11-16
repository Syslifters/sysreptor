import subprocess

from reportcreator_api import settings
from django.core.management.commands import dumpdata


def create_dump():

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
