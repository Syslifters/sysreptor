import logging
import shutil
import tempfile
from zipfile import ZipFile

from django.core.management.base import BaseCommand, CommandError, CommandParser

from sysreptor.api_utils.backup_utils import restore_backup
from sysreptor.management.commands.backup import aes_key, open_arg_file
from sysreptor.utils import crypto, license


class Command(BaseCommand):
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('file', nargs='?', default='-')
        parser.add_argument('--key', type=aes_key, help='AES key to decrypt the backup')
        parser.add_argument('--keepfiles', action='store_true', default=False, help='Keep existing files in storages. Do not delete them.')
        parser.add_argument('--skip-files', action='store_true', default=False, help='Skip restoring files from the backup')
        parser.add_argument('--skip-database', action='store_true', default=False, help='Skip restoring database from the backup')

    def handle(self, file, key, keepfiles, skip_files, skip_database, verbosity=1, **kwargs) -> str | None:
        if verbosity <= 0:
            logging.getLogger().disabled = True

        if not license.is_professional(skip_db_checks=True):
            raise CommandError('Professional license required')

        try:
            with tempfile.TemporaryFile(mode='w+b') as f:
                with open_arg_file(file, mode='rb') as raw:
                    stream = crypto.open(raw, key=key) if key else raw
                    try:
                        shutil.copyfileobj(stream, f)
                    finally:
                        if stream is not raw:
                            stream.close()
                f.seek(0)
                with ZipFile(file=f, mode='r') as z:
                    restore_backup(z, keepfiles=keepfiles, skip_files=skip_files, skip_database=skip_database)
        except crypto.CryptoError as ex:
            raise CommandError(*ex.args) from ex
