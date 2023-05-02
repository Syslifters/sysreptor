import itertools
import warnings
import copy
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.test import override_settings

from reportcreator_api.pentests.models import PentestFinding, PentestProject, ProjectType, UploadedAsset, UploadedImage, \
    UploadedProjectFile, UploadedUserNotebookImage, NotebookPage, UserPublicKey, ArchivedProjectKeyPart, ArchivedProjectPublicKeyEncryptedKeyPart
from reportcreator_api.users.models import MFAMethod, PentestUser, Session


class Command(BaseCommand):
    help = 'Encrypt all data using the current encryption key. If data was encrypted with a different key, it is re-encrypted with the current key.'

    def add_arguments(self, parser) -> None:
        parser.add_argument('--decrypt', action='store_true', help='Decrypt all data')

    def encrypt_data(self):
        # Encrypt DB fields
        PentestProject.objects.bulk_update(PentestProject.objects.all().iterator(), ['custom_fields'])
        PentestFinding.objects.bulk_update(PentestFinding.objects.all().iterator(), ['custom_fields', 'template_id'])
        ProjectType.objects.bulk_update(ProjectType.objects.all().iterator(), ['report_template', 'report_styles', 'report_preview_data'])
        NotebookPage.objects.bulk_update(NotebookPage.objects.all(), ['title', 'text'])
        PentestUser.objects.bulk_update(PentestUser.objects.all(), ['password'])
        Session.objects.bulk_update(Session.objects.all(), ['session_key', 'session_data'])
        MFAMethod.objects.bulk_update(MFAMethod.objects.all(), ['data'])
        UserPublicKey.objects.bulk_update(UserPublicKey.objects.all(), ['public_key'])
        ArchivedProjectKeyPart.objects.bulk_update(ArchivedProjectKeyPart.objects.all(), ['key_part'])
        ArchivedProjectPublicKeyEncryptedKeyPart.objects.bulk_update(ArchivedProjectPublicKeyEncryptedKeyPart.objects.all(), ['encrypted_data'])

        # Encrypt files
        old_files = []
        for f in itertools.chain(
                UploadedImage.objects.all(), 
                UploadedAsset.objects.all(), 
                UploadedUserNotebookImage.objects.all(),
                UploadedProjectFile.objects.all()
            ):
            # Copy file content. Encryption is performed during content copy to new file by the storage
            old_file = copy.copy(f.file)
            f.file.save(name=f.name, content=old_file, save=False)
            f.save()
            old_files.append(old_file)
        for f in old_files:
            f.storage.delete(f.name)

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
        

