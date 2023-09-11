import itertools
import warnings
import copy
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.test import override_settings
from reportcreator_api.pentests import storages

from reportcreator_api.pentests.models import PentestFinding, PentestProject, ProjectType, UploadedAsset, UploadedImage, \
    UploadedProjectFile, UploadedUserNotebookImage, UploadedUserNotebookFile, ProjectNotebookPage, UserNotebookPage, UserPublicKey, \
    ArchivedProjectKeyPart, ArchivedProjectPublicKeyEncryptedKeyPart, UploadedTemplateImage, ReportSection
from reportcreator_api.users.models import MFAMethod, PentestUser, Session


class Command(BaseCommand):
    help = 'Encrypt all data using the current encryption key. If data was encrypted with a different key, it is re-encrypted with the current key.'

    def add_arguments(self, parser) -> None:
        parser.add_argument('--decrypt', action='store_true', help='Decrypt all data')

    def encrypt_storage_files(self, storage, models):
        for m in list(models):
            if hasattr(m, 'history'):
                models.append(m.history.model)

        file_name_map = {}
        for model in models:
            data_list = model.objects.all().values('id', 'name', 'file')
            for data in data_list:
                if data['file'] not in file_name_map:
                    with storage.open(data['file'], mode='rb') as old_file:
                        file_name_map[data['file']] = storage.save(name='new', content=old_file)
                        storage.delete(name=data['file'])
                data['file'] = file_name_map[data['file']]
            model.objects.bulk_update(map(lambda d: model(**d), data_list), ['name', 'file'])

    def encrypt_db_fields(self, model, fields):
        model.objects.bulk_update(model.objects.all().iterator(), fields)
        if hasattr(model, 'history'):
            model.history.model.objects.bulk_update(model.history.model.objects.all().iterator(), fields)                    

    def encrypt_data(self):
        # Encrypt DB fields
        self.encrypt_db_fields(PentestProject, ['unknown_custom_fields'])
        self.encrypt_db_fields(ReportSection, ['custom_fields'])
        self.encrypt_db_fields(PentestFinding, ['custom_fields', 'template_id'])
        self.encrypt_db_fields(ProjectType, ['report_template', 'report_styles', 'report_preview_data'])
        self.encrypt_db_fields(ProjectNotebookPage, ['title', 'text'])
        self.encrypt_db_fields(UserNotebookPage, ['title', 'text'])
        self.encrypt_db_fields(PentestUser, ['password'])
        self.encrypt_db_fields(Session, ['session_key', 'session_data'])
        self.encrypt_db_fields(MFAMethod, ['data'])
        self.encrypt_db_fields(UserPublicKey, ['public_key'])
        self.encrypt_db_fields(ArchivedProjectKeyPart, ['key_part'])
        self.encrypt_db_fields(ArchivedProjectPublicKeyEncryptedKeyPart, ['encrypted_data'])

        # Encrypt files
        self.encrypt_storage_files(storages.get_uploaded_asset_storage(), [UploadedAsset])
        self.encrypt_storage_files(storages.get_uploaded_image_storage(), [UploadedImage, UploadedTemplateImage, UploadedUserNotebookImage])
        self.encrypt_storage_files(storages.get_uploaded_file_storage(), [UploadedProjectFile, UploadedUserNotebookFile])

    def handle(self, decrypt, *args, **options):
        if not settings.ENCRYPTION_KEYS:
            raise CommandError('No ENCRYPTION_KEYS configured')

        if decrypt:
            if settings.DEFAULT_ENCRYPTION_KEY_ID:
                warnings.warn('A DEFAULT_ENCRYPTION_KEY_ID is configured. New and updated data will be encrypted while storing it. Set DEFAULT_ENCRYPTION_KEY_ID=None to permanently disable encryption.')

            with override_settings(DEFAULT_ENCRYPTION_KEY_ID=None, ENCRYPTION_PLAINTEXT_FALLBACK=True):
                self.encrypt_data()
        else:
            if not settings.DEFAULT_ENCRYPTION_KEY_ID:
                raise CommandError('No DEFAULT_ENCRYPTION_KEY_ID configured')
            if not settings.ENCRYPTION_KEYS.get(settings.DEFAULT_ENCRYPTION_KEY_ID):
                raise CommandError('Invalid DEFAULT_ENCRYPTION_KEY_ID')
            with override_settings(ENCRYPTION_PLAINTEXT_FALLBACK=True):
                self.encrypt_data()
        

