import pytest
import base64
import io
import zipfile
from datetime import datetime
from django.conf import settings
from django.forms import model_to_dict
from django.http import StreamingHttpResponse
from django.urls import reverse
from django.test import override_settings
from django.core import serializers
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command, CommandError

from reportcreator_api.archive import crypto
from reportcreator_api.archive.crypto.base import EncryptionKey
from reportcreator_api.notifications.models import NotificationSpec
from reportcreator_api.pentests.models import UploadedImage
from reportcreator_api.tests.mock import api_client, create_archived_project, create_png_file, create_project, create_project_type, create_template, create_user
from reportcreator_api.api_utils.backup_utils import destroy_database
from reportcreator_api.management.commands import restorebackup


@pytest.mark.django_db
class TestBackup:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.backup_key = 'a' * 30
        with override_settings(
            BACKUP_KEY=self.backup_key,
            ENCRYPTION_KEYS={'test-key': crypto.EncryptionKey(id='test-key', key=b'a' * 32)},
            DEFAULT_ENCRYPTION_KEY_ID='test-key',
            ENCRYPTION_PLAINTEXT_FALLBACK=False,
        ):
            self.user_system = create_user(is_system_user=True)

            # Data to be backed up
            self.user = create_user(mfa=True)
            self.project = create_project()
            self.image_history_only = UploadedImage.objects.create(
                linked_object=self.project, name='file-deleted.png', file=SimpleUploadedFile(name=f'file-deleted.png', content=create_png_file()))
            self.image_history_only.delete()
            self.project_type = create_project_type()
            self.template = create_template()
            self.archived_project = create_archived_project()
            self.notification = NotificationSpec.objects.create(title='test', text='test')
            
            yield

    def assert_backup_obj(self, backup, obj):
        data = next(filter(lambda e: e.object.pk == obj.pk, backup))
        assert data.object == obj
        obj_formatted = model_to_dict(obj)
        if 'history_date' in obj_formatted:
            # Strip microseconds for comparison (stripped by serializer)
            df = obj_formatted['history_date'].isoformat()
            obj_formatted['history_date'] = datetime.fromisoformat(df[:23] + df[26:])
        assert model_to_dict(data.object) == obj_formatted
        return data
    
    def assert_backup_file(self, backup, z, dir, obj, stored_encrypted=False):
        if obj.pk:
            self.assert_backup_obj(backup, obj)
        bak_img = z.read(f'{dir}/{obj.file.name}')
        assert bak_img.startswith(crypto.MAGIC) == stored_encrypted
        assert bak_img == obj.file.open('rb').read()

    def assert_backup(self, content):
        with zipfile.ZipFile(io.BytesIO(content), mode='r') as z:
            assert zipfile.Path(z, 'VERSION').read_text() == settings.VERSION
            assert zipfile.Path(z, 'migrations.json').exists()

            # Test that data is not encrypted in backup
            assert crypto.MAGIC not in z.read('backup.jsonl')
            backup = list(serializers.deserialize('jsonl', z.read('backup.jsonl')))

            # Test if objects are present in backup
            for o in [
                self.project, self.project.history.first(),
                self.project.findings.first(), self.project.findings.first().history.first(),
                self.project.sections.first(), self.project.sections.first().history.first(),
                self.project.notes.first(), self.project.notes.first().history.first(),
                self.project_type, self.project_type.history.first(),
                self.template, self.template.history.first(),
                self.template.main_translation, self.template.main_translation.history.first(),
                self.user.notes.first(),
                self.user.mfa_methods.first(),
                self.archived_project,
                self.notification,
                self.user.notifications.first(),
            ]:
                self.assert_backup_obj(backup, o)

            self.assert_backup_file(backup, z, 'uploadedimages', self.project.images.all().first())
            self.assert_backup_file(backup, z, 'uploadedimages', self.user.images.all().first())
            self.assert_backup_file(backup, z, 'uploadedimages', self.template.images.all().first())
            self.assert_backup_file(backup, z, 'uploadedimages', self.image_history_only)
            self.assert_backup_file(backup, z, 'uploadedassets', self.project_type.assets.all().first())
            self.assert_backup_file(backup, z, 'uploadedfiles', self.project.files.first())
            self.assert_backup_file(backup, z, 'uploadedfiles', self.user.files.all().first())
            self.assert_backup_file(backup, z, 'archivedfiles', self.archived_project, stored_encrypted=True)

    def backup_request(self, user=None, backup_key=None, aes_key=None):
        if not user:
            user = self.user_system
        if not backup_key:
            backup_key = self.backup_key
        return api_client(user).post(reverse('utils-backup'), data={'key': backup_key, 'aes_key': base64.b64encode(aes_key).decode() if aes_key else None})
    
    def test_backup(self):
        # Create backup
        res = self.backup_request()
        assert res.status_code == 200
        assert isinstance(res, StreamingHttpResponse)
        z = b''.join(res.streaming_content)
        self.assert_backup(z)
        
    def test_backup_permissions(self):
        user_regular = create_user()
        assert self.backup_request(user=user_regular).status_code == 403
        superuser = create_user(is_superuser=True)
        assert self.backup_request(user=superuser).status_code == 403

    def test_invalid_backup_key(self):
        assert self.backup_request(backup_key=b'invalid' * 10).status_code == 400

    def test_backup_encryption(self):
        aes_key = b'a' * 32
        res = self.backup_request(aes_key=aes_key)
        assert res.status_code == 200
        assert isinstance(res, StreamingHttpResponse)
        enc = b''.join(res.streaming_content)
        assert enc.startswith(crypto.MAGIC)
        with crypto.open(fileobj=io.BytesIO(enc), key=crypto.EncryptionKey(id=None, key=aes_key)) as c:
            assert c.metadata['key_id'] is None
            z = c.read()
            self.assert_backup(z)


@pytest.mark.django_db
class TestBackupRestore:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.backup_key = 'a' * 30
        self.backup_encryption_key = b'b' * 32
        with override_settings(
            BACKUP_KEY=self.backup_key,
            ENCRYPTION_KEYS={'test-key': crypto.EncryptionKey(id='test-key', key=b'a' * 32)},
            DEFAULT_ENCRYPTION_KEY_ID='test-key',
            ENCRYPTION_PLAINTEXT_FALLBACK=False,
        ):
            self.user_system = create_user(is_system_user=True)

            # Data to be backed up
            self.user = create_user(mfa=True)
            self.project = create_project()
            self.project_type = create_project_type()
            self.template = create_template()
            self.archived_project = create_archived_project()

            yield

    def backup_request(self, aes_key=None):
        return api_client(self.user_system).post(reverse('utils-backup'), data={'key': self.backup_key, 'aes_key': base64.b64encode(aes_key).decode() if aes_key else None})
    
    def delete_file(self, file_obj):
        file_name = file_obj.file.name
        file_content = file_obj.file.read()
        file_obj.file.storage.delete(file_name)
        return {
            'obj': file_obj, 
            'name': file_name, 
            'content': file_content,
        }

    def test_backup_restore(self):
        # Create backup
        backup = b''.join(self.backup_request(aes_key=self.backup_encryption_key).streaming_content)

        # Delete files
        deleted_files = [
            self.delete_file(self.project.images.first()),
            self.delete_file(self.project.files.first()),
            self.delete_file(self.project_type.assets.first()),
            self.delete_file(self.template.images.first()),
            self.delete_file(self.user.images.first()),
            self.delete_file(self.user.files.first()),
            self.delete_file(self.archived_project),
        ]
        # Delete DB data
        destroy_database()

        # Restore backup
        call_command(restorebackup.Command(), file=io.BytesIO(backup), key=EncryptionKey(id=None, key=self.backup_encryption_key), keepfiles=True)
        
        # Validate restored data
        self.project.refresh_from_db()
        self.project_type.refresh_from_db()
        self.template.refresh_from_db()
        self.user.refresh_from_db()
        self.archived_project.refresh_from_db()

        # Validate restored files
        for f in deleted_files:
            fo = f['obj']
            fo.refresh_from_db()
            assert fo.file.name == f['name']
            assert fo.file.read() == f['content']

    def test_backup_restore_damaged(self):
        backup = b''.join(self.backup_request(aes_key=self.backup_encryption_key).streaming_content)
        backup = backup[:len(backup) - 100]

        with pytest.raises(CommandError):
            call_command(restorebackup.Command(), file=io.BytesIO(backup), key=EncryptionKey(id=None, key=self.backup_encryption_key), keepfiles=True)

