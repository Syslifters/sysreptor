import json
import logging
import os
import sys
from typing import BinaryIO, TextIO

from django.core.management.base import BaseCommand, CommandError, CommandParser

from sysreptor.api_utils.backup_utils import create_backup, encrypt_backup, to_chunks, upload_to_s3_bucket
from sysreptor.api_utils.serializers import S3ParamsSerializer
from sysreptor.utils import crypto, license


def aes_key(val):
    key = bytes.fromhex(val)
    if len(key) != 32:
        raise ValueError('256-bit AES key required')
    return crypto.EncryptionKey(id=None, key=key)


def parse_s3_params(val):
    return S3ParamsSerializer(json.loads(val)).data


def open_arg_file(path_or_file: str | os.PathLike | BinaryIO | TextIO, mode: str = 'rb') -> BinaryIO | TextIO:
    """Open a CLI file argument after argparse parsing (replacement for deprecated FileType)."""
    if not isinstance(path_or_file, str | os.PathLike):
        return path_or_file
    elif path_or_file == '-':
        if 'r' in mode:
            return sys.stdin.buffer if 'b' in mode else sys.stdin
        if any(c in mode for c in 'wax'):
            return sys.stdout.buffer if 'b' in mode else sys.stdout
        raise CommandError(f'argument "-" not allowed with mode {mode!r}')
    else:
        try:
            return open(path_or_file, mode)
        except OSError as ex:
            raise CommandError(f"can't open '{path_or_file}': {ex}") from ex


class Command(BaseCommand):
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('file', nargs='?', default='-')
        parser.add_argument('--key', type=aes_key, help='AES key as hex string to encrypt the backup (optional)')
        parser.add_argument('--s3-params', type=parse_s3_params, help='S3 parameters for uploading the backup to S3 (optional)')

    def handle(self, file, key, s3_params=None, verbosity=1, **kwargs) -> str | None:
        if verbosity <= 0:
            logging.getLogger().disabled = True

        if not license.is_professional(skip_db_checks=True):
            raise CommandError('Professional license required')

        # Create backup iterator
        z = create_backup(user=None)
        if key:
            z = encrypt_backup(z, key.key)

        if s3_params:
            upload_to_s3_bucket(z, s3_params)
        else:
            # Write backup to file
            with open_arg_file(file, mode='wb') as f:
                for c in to_chunks(z):
                    f.write(c)

