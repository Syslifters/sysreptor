import argparse
import logging

from django.core.management.base import BaseCommand, CommandError, CommandParser

from sysreptor.api_utils.backup_utils import create_backup, encrypt_backup, to_chunks
from sysreptor.api_utils.models import BackupLog, BackupLogType
from sysreptor.utils import crypto, license


def aes_key(val):
    key = bytes.fromhex(val)
    if len(key) != 32:
        raise ValueError('256-bit AES key required')
    return crypto.EncryptionKey(id=None, key=key)


class Command(BaseCommand):
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('file', nargs='?', type=argparse.FileType('wb'), default='-')
        parser.add_argument('--key', type=aes_key, help='AES key to encrypt the backup (optional)')

    def handle(self, file, key, verbosity=1, **kwargs) -> str | None:
        if verbosity <= 0:
            logging.getLogger().disabled = True

        if not license.is_professional(skip_db_checks=True):
            raise CommandError('Professional license required')

        # Create backup iterator
        z = create_backup(user=None)
        if key:
            z = encrypt_backup(z, key.key)

        # Write backup to file
        with file:
            for c in to_chunks(z):
                file.write(c)

        BackupLog.objects.create(type=BackupLogType.BACKUP_FINISHED, user=None)
        logging.info('Backup finished')
