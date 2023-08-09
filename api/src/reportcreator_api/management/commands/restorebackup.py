import argparse
import shutil
import tempfile
from zipfile import ZipFile
from django.core.management.base import BaseCommand, CommandError, CommandParser
from reportcreator_api.api_utils.backup_utils import restore_backup
from reportcreator_api.archive import crypto

from reportcreator_api.utils import license
from reportcreator_api.management.commands.backup import aes_key


class Command(BaseCommand):
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('file', nargs='?', type=argparse.FileType('rb'), default='-')
        parser.add_argument('--key', type=aes_key, help='AES key to decrypt the backup')
        parser.add_argument('--keepfiles', action='store_true', default=False, help='Keep existing files in storages. Do not delete them.')

    def handle(self, file, key, keepfiles, **kwargs) -> str | None:
        if not license.is_professional():
            raise CommandError('Professional license required')
        
        if key:
            file = crypto.open(file, key=key)
        
        try:
            with tempfile.TemporaryFile(mode='w+b') as f:
                shutil.copyfileobj(file, f)
                file.close()
                f.seek(0)

                with ZipFile(file=f, mode='r') as z:
                    restore_backup(z, keepfiles=keepfiles)
        except crypto.CryptoError as ex:
            raise CommandError(*ex.args) from ex

