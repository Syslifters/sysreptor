import logging
import warnings

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.test import override_settings

from sysreptor.utils.crypto.fields import EncryptedField
from sysreptor.utils.crypto.storage import EncryptedStorageMixin
from sysreptor.utils.files import get_all_file_fields
from sysreptor.utils.utils import groupby_to_dict


class Command(BaseCommand):
    help = 'Encrypt all data using the current encryption key. If data was encrypted with a different key, it is re-encrypted with the current key.'

    def add_arguments(self, parser) -> None:
        parser.add_argument('--decrypt', action='store_true', help='Decrypt all data')

    def encrypt_data(self):
        # Encrypt DB fields
        logging.info('Encrypting DB fields')
        for model in apps.get_models():
            encrypted_fields = []
            for field in model._meta.get_fields():
                if isinstance(field, EncryptedField):
                    encrypted_fields.append(field.name)
            if encrypted_fields:
                logging.info(f'  Encrypting DB fields for model {model._meta.label}: {", ".join(encrypted_fields)}')
                model.objects.bulk_update(model.objects.all().iterator(), encrypted_fields)

        # Encrypt files and file DB fields
        for storage_name, fields in groupby_to_dict(get_all_file_fields(), key=lambda f: f['storage_name']).items():
            storage = fields[0]['storage']
            if not isinstance(storage, EncryptedStorageMixin):
                continue
            logging.info(f'Encrypting files for storage {storage_name}')
            file_name_map = {}
            for field_info in fields:
                model = field_info['model']
                field_name = field_info['field_name']
                logging.info(f'  Encrypting file field {model._meta.label}.{field_name} in storage {storage_name}')
                data_list = list(model.objects.all().values('pk', field_name))
                history_list = list(model.history.all().values('pk', field_name)) if hasattr(model, 'history') else []
                for data in data_list + history_list:
                    if data[field_name] not in file_name_map:
                        try:
                            with storage.open(data[field_name], mode='rb') as old_file:
                                file_name_map[data[field_name]] = storage.save(name='new', content=old_file)
                                storage.delete(name=data[field_name])
                        except (FileNotFoundError, OSError):
                            file_name_map[data[field_name]] = data[field_name]
                            logging.warning(f'    File "{data[field_name]}" not found in storage "{storage_name}". Skipping.')
                    data[field_name] = file_name_map[data[field_name]]
                model.objects.bulk_update(map(lambda d: model(**d), data_list), [field_name])
                if hasattr(model, 'history'):
                    model.history.model.objects.bulk_update(map(lambda d: model.history.model(**d), history_list), [field_name])

    def handle(self, decrypt, *args, **options):
        if not settings.ENCRYPTION_KEYS:
            raise CommandError('No ENCRYPTION_KEYS configured')

        if decrypt:
            if settings.DEFAULT_ENCRYPTION_KEY_ID:
                warnings.warn('A DEFAULT_ENCRYPTION_KEY_ID is configured. New and updated data will be encrypted while storing it. Set DEFAULT_ENCRYPTION_KEY_ID=None to permanently disable encryption.', stacklevel=1)

            with override_settings(DEFAULT_ENCRYPTION_KEY_ID=None, ENCRYPTION_PLAINTEXT_FALLBACK=True):
                self.encrypt_data()
        else:
            if not settings.DEFAULT_ENCRYPTION_KEY_ID:
                raise CommandError('No DEFAULT_ENCRYPTION_KEY_ID configured')
            if not settings.ENCRYPTION_KEYS.get(settings.DEFAULT_ENCRYPTION_KEY_ID):
                raise CommandError('Invalid DEFAULT_ENCRYPTION_KEY_ID')
            with override_settings(ENCRYPTION_PLAINTEXT_FALLBACK=True):
                self.encrypt_data()


