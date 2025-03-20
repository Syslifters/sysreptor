import logging
from collections.abc import Iterable
from pathlib import Path

from django.conf import settings
from django.core.files.storage import storages
from django.core.management.base import BaseCommand
from storages.backends.s3 import S3Storage

from sysreptor.utils import crypto
from sysreptor.utils.crypto.storage import EncryptedStorageMixin


def walk_filesystem(path: Path) -> Iterable[Path]:
    for e in path.iterdir():
        if e.is_file():
            yield e
        elif e.is_dir():
            yield from walk_filesystem(e)


class Command(BaseCommand):
    help = 'Move files from local filesystem storage to S3. S3 needs to be configured as the default storage.'

    def add_arguments(self, parser) -> None:
        parser.add_argument('--skip-existing', action='store_true', help='Do not upload files that already exist on S3')

    def handle(self, skip_existing=False, *args, **options):
        for storage_name in storages.backends.keys() - {'staticfiles'}:
            self.move_files_to_s3(storage_name=storage_name, skip_existing=skip_existing)

    def move_files_to_s3(self, storage_name, skip_existing=False):
        storage = storages[storage_name]
        if not isinstance(storage, S3Storage):
            logging.warning(f'Storage "{storage_name}" is not an S3 storage. Skipping.')
            return

        path = settings.MEDIA_ROOT / (storage_name.replace('_', ''))
        if not path.is_dir():
            logging.warning(f'Storage "{storage_name}": Directory "{path.absolute()}" does not exist on filesystem. Skipping.')
            return

        logging.info(f'Storage "{storage_name}": Moving files to S3...')
        for file in walk_filesystem(path):
            filename = str(file.relative_to(path))
            try:
                if skip_existing and storage.exists(filename):
                    logging.info(f'    File "{file}" already exists on S3. Skipping.')
                    continue

                try:
                    with crypto.open(file.open('rb'), mode='r', plaintext_fallback=True) if isinstance(storage, EncryptedStorageMixin) else file.open('rb') as f_src:
                        with storage.open(filename, 'wb') as f_dest:
                            for chunk in f_src.chunks():
                                f_dest.write(chunk)
                except crypto.CryptoError as ex:
                    logging.error(f'    File "{file}": {ex}')
            except Exception as ex:
                logging.error(f'    Error moving file "{file}" to S3: {ex}')

        logging.info(f'Storage "{storage_name}": Done.')
