from datetime import timedelta

import pytest
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string

from sysreptor.api_utils.models import BackupLog, BackupLogType
from sysreptor.audit.models import AuditLogEntry, AuditLogTypes
from sysreptor.pentests.models import PentestProject, ProjectMemberInfo
from sysreptor.tasks.models import LicenseActivationInfo
from sysreptor.tests.mock import (
    api_client,
    create_project,
    create_project_type,
    create_user,
)
from sysreptor.tests.utils import assertKeysEqual
from sysreptor.users.models import APIToken, AuthIdentity, MFAMethod
from sysreptor.utils import license
from sysreptor.utils.configuration import configuration


@pytest.mark.django_db()
class TestAuditLog:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user(username='user', is_superuser=True, admin_permissions_enabled=True)
        self.client = api_client(self.user)
        AuditLogEntry.objects.all().delete()

    def test_entries_survive_delete(self):
        res = self.client.post(reverse('pentestproject-list'), data={
            'name': 'test-project',
            'project_type': create_project_type().id,
            'members': [{'id': self.user.id}],
        })
        project = PentestProject.objects.get(id=res.data['id'])
        user_id = self.user.id
        entry = AuditLogEntry.objects.get(type=AuditLogTypes.PROJECT_MEMBER_ADDED, actor=self.user, object_id=project.id)
        self.user.delete()
        project.delete()
        entry.refresh_from_db()
        assert entry.actor_id == user_id
        assert entry.data['actor_name'] == f'{self.user.username} ({self.user.name})'
        assert str(entry.object_id) == res.data['id']
        assert entry.data['related_name'] == project.name

    def test_user_create(self):
        user = create_user(username='new-user')
        assert AuditLogEntry.objects.all().count() == 1
        assert AuditLogEntry.objects.get(type=AuditLogTypes.USER_CREATED, object_id=user.id)

    def test_user_delete(self):
        user_id = self.user.id
        self.user.delete()
        assert AuditLogEntry.objects.all().count() == 1
        assert AuditLogEntry.objects.get(type=AuditLogTypes.USER_DELETED, object_id=user_id)

    def test_login(self):
        password = get_random_string(32)
        self.user.set_password(password)
        self.user.save()
        self.client.post(reverse('auth-login'), data={'username': self.user.username, 'password': password})
        entry = AuditLogEntry.objects.get(type=AuditLogTypes.LOGIN_SUCCESS, actor=self.user, object_id=self.user.id)
        assert entry.data['method'] == 'local'

    def test_login_mfa(self):
        password = get_random_string(32)
        self.user.set_password(password)
        self.user.save()
        mfa = MFAMethod.objects.create_backup(user=self.user)
        code = mfa.data['backup_codes'][0]

        client = api_client()
        res = client.post(reverse('auth-login'), data={'username': self.user.username, 'password': password})
        assert res.status_code == 200
        assert res.data['status'] == 'mfa-required'

        res = client.post(reverse('auth-login-code'), data={'id': str(mfa.id), 'code': code})
        assert res.status_code == 200
        assert res.data['status'] == 'success'

        entry = AuditLogEntry.objects.get(type=AuditLogTypes.LOGIN_SUCCESS, actor=self.user, object_id=self.user.id)
        assertKeysEqual(entry.data, {
            'method': 'local',
            'mfa': {
                'id': str(mfa.id),
                'method_type': mfa.method_type,
                'name': mfa.name,
            },
        })

    def test_logout(self):
        self.client.post(reverse('auth-logout'))
        assert AuditLogEntry.objects.get(type=AuditLogTypes.LOGOUT, actor=self.user, object_id=self.user.id)

    def test_admin_enable_disable(self):
        self.user.admin_permissions_enabled = False
        session = self.client.session
        session.update({'admin_permissions_enabled': False, 'authentication_info': {'reauth_time': timezone.now().isoformat()}})
        session.save()

        res = self.client.post(reverse('pentestuser-enable-admin-permissions'))
        assert res.status_code == 200
        assert AuditLogEntry.objects.get(type=AuditLogTypes.ADMIN_ENABLED, actor=self.user, object_id=self.user.id)

        self.client.post(reverse('pentestuser-disable-admin-permissions'))
        assert AuditLogEntry.objects.get(type=AuditLogTypes.ADMIN_DISABLED, actor=self.user, object_id=self.user.id)

    def test_mfa_create(self):
        mfa = MFAMethod.objects.create_backup(user=self.user)
        entry = AuditLogEntry.objects.get(type=AuditLogTypes.MFA_CREATED, object_id=self.user.id)
        assertKeysEqual(entry.data, {
            'mfa': {
                'id': str(mfa.id),
                'method_type': mfa.method_type,
                'name': mfa.name,
            },
        })

    def test_mfa_delete(self):
        mfa = MFAMethod.objects.create_backup(user=self.user)
        mfa_id = mfa.id
        mfa.delete()

        entry = AuditLogEntry.objects.get(type=AuditLogTypes.MFA_DELETED, object_id=self.user.id)
        assertKeysEqual(entry.data, {
            'mfa': {
                'id': str(mfa_id),
                'method_type': mfa.method_type,
                'name': mfa.name,
            },
        })

    def test_apitoken_create(self):
        token = APIToken.objects.create(user=self.user, name='audit-token')
        entry = AuditLogEntry.objects.get(type=AuditLogTypes.API_TOKEN_CREATED, object_id=self.user.id)
        assertKeysEqual(entry.data, {
            'api_token': {
                'id': str(token.id),
                'name': token.name,
                'expire_date': token.expire_date,
                'admin_permissions_enabled': token.admin_permissions_enabled,
            },
        })

    @pytest.mark.parametrize(('data', 'expected'), [
        ({'is_superuser': True}, AuditLogTypes.USER_PERMISSIONS_UPDATED),
        ({'is_project_admin': True}, AuditLogTypes.USER_PERMISSIONS_UPDATED),
        ({'is_user_manager': True}, AuditLogTypes.USER_PERMISSIONS_UPDATED),
        ({'is_designer': True}, AuditLogTypes.USER_PERMISSIONS_UPDATED),
        ({'is_template_editor': True}, AuditLogTypes.USER_PERMISSIONS_UPDATED),
        ({'is_guest': True}, AuditLogTypes.USER_PERMISSIONS_UPDATED),
        ({'is_global_archiver': True}, AuditLogTypes.USER_PERMISSIONS_UPDATED),
        ({'username': 'new-username'}, AuditLogTypes.USER_UPDATED),
        ({'email': 'new@example.com'}, AuditLogTypes.USER_UPDATED),
        ({'is_active': False}, AuditLogTypes.USER_UPDATED),
        ({'can_login_local': False}, AuditLogTypes.USER_UPDATED),
        ({'first_name': 'Example', 'last_name': 'User'}, None),
    ])
    def test_user_update(self, data, expected):
        user = create_user(username='target-user')
        AuditLogEntry.objects.all().delete()

        self.client.patch(reverse('pentestuser-detail', kwargs={'pk': user.id}), data=data)
        entry = AuditLogEntry.objects.first()
        if expected:
            assert entry is not None
            assert entry.type == expected
            assert entry.actor == self.user
            assert entry.related == user
            assert entry.data['changes'].keys() == data.keys()
        else:
            assert not entry

    def test_password_reset(self):
        user = create_user(username='reset-user', password=get_random_string(32))
        self.client.post(reverse('pentestuser-reset-password', kwargs={'pk': user.id}), data={
            'password': get_random_string(32),
        })
        assert AuditLogEntry.objects.get(type=AuditLogTypes.PASSWORD_CHANGED, actor=self.user, object_id=user.id)

    def test_password_forgot(self):
        self.client.post(reverse('auth-forgot-password-reset'), data={
            'user': self.user.id,
            'token': default_token_generator.make_token(self.user),
            'password': get_random_string(32),
        })
        assert AuditLogEntry.objects.get(type=AuditLogTypes.PASSWORD_CHANGED, object_id=self.user.id)

    def test_auth_identity(self):
        data = {'provider': 'remoteuser', 'identifier': 'ext-id'}
        identity = AuthIdentity.objects.create(user=self.user, **data)
        entry_created = AuditLogEntry.objects.get(type=AuditLogTypes.AUTH_IDENTITY_CREATED, object_id=self.user.id)
        assertKeysEqual(entry_created.data, {'auth_identity': data})

        identity.delete()
        entry_deleted = AuditLogEntry.objects.get(type=AuditLogTypes.AUTH_IDENTITY_DELETED, object_id=self.user.id)
        assertKeysEqual(entry_deleted.data, {'auth_identity': data})

    def test_project_member(self):
        project = create_project()
        member = ProjectMemberInfo.objects.create(project=project, user=self.user)

        entry = AuditLogEntry.objects.get(type=AuditLogTypes.PROJECT_MEMBER_ADDED, object_id=project.id)
        expected = {
            'member': {
                'id': str(self.user.id),
                'username': self.user.username,
            },
            'project': {
                'id': str(project.id),
                'name': project.name,
            },
        }
        assertKeysEqual(entry.data, expected)

        member.delete()
        entry = AuditLogEntry.objects.get(type=AuditLogTypes.PROJECT_MEMBER_REMOVED, object_id=project.id)
        assertKeysEqual(entry.data, expected)

    @pytest.mark.parametrize(('backup_type', 'expected'), [
        (BackupLogType.BACKUP_STARTED, True),
        (BackupLogType.RESTORE, True),
        (BackupLogType.BACKUP_FINISHED, False),
        (BackupLogType.SETUP, False),
    ])
    def test_backup_events_logged(self, backup_type, expected):
        BackupLog.objects.create(type=backup_type, user=self.user)
        entry = AuditLogEntry.objects.filter(type=backup_type.value).order_by('-created').first()
        if expected:
            assert entry.actor == self.user
            assert entry.data['related_name'] == backup_type.value
        else:
            assert not entry

    def test_settings_changed(self):
        configuration.update({
            'GUEST_USERS_CAN_EDIT_PROJECTS': False,
            'OIDC_AUTHLIB_OAUTH_CLIENTS': '{"oidc": {"label": "OIDC", "client_id": "id", "client_secret": "super-secret"}}',
        }, only_changed=False)

        entry = AuditLogEntry.objects.get(type=AuditLogTypes.SETTINGS_CHANGED, object_id=None)
        assert set(entry.data['changes']) == {'GUEST_USERS_CAN_EDIT_PROJECTS', 'OIDC_AUTHLIB_OAUTH_CLIENTS'}

    def test_license_changed(self):
        info = LicenseActivationInfo.objects.create(
            license_type=license.LicenseType.PROFESSIONAL,
            license_hash='test-license-hash',
        )
        entry = AuditLogEntry.objects.get(type=AuditLogTypes.LICENSE_CHANGED, object_id=info.id)
        assert entry.data['related_name'] == license.LicenseType.PROFESSIONAL
        assertKeysEqual(entry.data['license'], {
            'type': license.LicenseType.PROFESSIONAL,
            'hash': 'test-license-hash',
        })

    def test_share_projectnote(self):
        p = create_project()
        n = p.notes.first()
        res = self.client.post(reverse('projectnoteshareinfo-list', kwargs={'project_pk': p.id, 'note_id': n.note_id}), data={
            'password': get_random_string(32),
            'permissions_write': True,
            'expire_date': (timezone.now() + timedelta(days=30)).date().isoformat(),
        })

        entry = AuditLogEntry.objects.get(type=AuditLogTypes.NOTE_SHARE_CREATED, actor=self.user, object_id=n.id)
        assertKeysEqual(entry.data['share'], {
            'id': res.data['id'],
            'password_protected': True,
            'permissions_write': True,
        })
        assertKeysEqual(entry.data['note'], {
            'id': str(n.note_id),
            'title': n.title,
        })
        assertKeysEqual(entry.data['project'], {
            'id': str(p.id),
            'name': p.name,
        })
        assert 'password' not in entry.data['share']

    def test_share_usernote(self):
        n = self.user.notes.first()
        res = self.client.post(reverse('usernoteshareinfo-list', kwargs={'pentestuser_pk': self.user.id, 'note_id': n.note_id}), data={
            'password': get_random_string(32),
            'permissions_write': True,
            'expire_date': (timezone.now() + timedelta(days=30)).date().isoformat(),
        })

        entry = AuditLogEntry.objects.get(type=AuditLogTypes.NOTE_SHARE_CREATED, actor=self.user, object_id=n.id)
        assertKeysEqual(entry.data['share'], {
            'id': res.data['id'],
            'password_protected': True,
            'permissions_write': True,
        })
        assertKeysEqual(entry.data['note'], {
            'id': str(n.note_id),
            'title': n.title,
        })
        assertKeysEqual(entry.data['user'], {
            'id': str(self.user.id),
            'username': self.user.username,
        })
