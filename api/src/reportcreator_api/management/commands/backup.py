import argparse

from django.core.management.base import BaseCommand, CommandError, CommandParser

from reportcreator_api.api_utils.backup_utils import create_backup, encrypt_backup, to_chunks
from reportcreator_api.archive import crypto
from reportcreator_api.utils import license


def aes_key(val):
    key = bytes.fromhex(val)
    if len(key) != 32:
        raise ValueError('256-bit AES key required')
    return crypto.EncryptionKey(id=None, key=key)


class Command(BaseCommand):
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('file', nargs='?', type=argparse.FileType('wb'), default='-')
        parser.add_argument('--key', type=aes_key, help='AES key to encrypt the backup (optional)')

    def handle(self, file, key, **kwargs) -> str | None:
        if not license.is_professional(skip_db_checks=True):
            raise CommandError('Professional license required')

        # Create backup iterator
        z = create_backup()
        if key:
            z = encrypt_backup(z, key.key)

        # Write backup to file
        for c in to_chunks(z):
            file.write(c)

