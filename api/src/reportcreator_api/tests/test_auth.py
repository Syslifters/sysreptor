import pytest
import pyotp
from django.conf import settings
from django.urls import reverse
from django.test import override_settings

from reportcreator_api.utils.utils import omit_keys
from reportcreator_api.tests.mock import create_project, create_user, mock_time, api_client
from reportcreator_api.users.models import AuthIdentity, MFAMethod, MFAMethodType



@pytest.mark.django_db
class TestLogin:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.password = 'Password1!'
        self.user = create_user(username='user', password=self.password)
        self.user_mfa = create_user(username='user_mfa', password=self.password)
        self.mfa_backup = MFAMethod.objects.create_backup(user=self.user_mfa)
        self.mfa_totp = MFAMethod.objects.create_totp(user=self.user_mfa)

        self.client = api_client()

    def assert_api_access(self, expected):
        res = self.client.get(reverse('pentestuser-self'))
        if expected:
            assert res.status_code == 200
        else:
            assert res.status_code in [401, 403]

    def assert_login(self, user, password=None, success=True, status='success'):
        res = self.client.post(reverse('auth-login'), data={
            'username': user.username,
            'password': password or self.password,
        })
        if success:
            assert res.status_code == 200
            assert res.data['status'] == status
        else:
            assert res.status_code in [400, 403]
            self.assert_api_access(False)
        return res
    
    def assert_mfa_login(self, mfa_method, data=None, user=None, success=True):
        self.assert_login(user=user or self.user_mfa, status='mfa-required')
        if mfa_method.method_type == MFAMethodType.BACKUP:
            res = self.client.post(reverse('auth-login-code'), data={
                'id': str(mfa_method.id),
                'code': mfa_method.data['backup_codes'][0],
            } | (data or {}))
        elif mfa_method.method_type == MFAMethodType.TOTP:
            res = self.client.post(reverse('auth-login-code'), data=data or {
                'id': str(mfa_method.id),
                'code': pyotp.TOTP(**mfa_method.data).now(),
            })
        elif mfa_method.method_type == MFAMethodType.FIDO2:
            pass
        
        if success:
            assert res.status_code == 200
            self.assert_api_access(True)
        else:
            assert res.status_code in [400, 403]
            self.assert_api_access(False)
        return res
    
    def test_login(self):
        self.assert_login(user=self.user)
        self.assert_api_access(True)

    def test_logout(self):
        self.assert_login(self.user)
        res = self.client.post(reverse('auth-logout'))
        assert res.status_code == 204
        self.assert_api_access(False)
    
    def test_login_failure(self):
        self.assert_login(user=self.user, password='invalid_password', success=False)
    
    def test_login_mfa(self):
        self.assert_login(user=self.user_mfa, status='mfa-required')
        self.assert_api_access(False)

    def test_login_timeout(self):
        with mock_time(before=settings.MFA_LOGIN_TIMEOUT * 2):
            self.assert_login(user=self.user_mfa, status='mfa-required')
        res = self.client.post(reverse('auth-login-code'), data={
                'id': str(self.mfa_totp.id),
                'code': pyotp.TOTP(**self.mfa_totp.data).now(),
            })
        assert res.status_code == 400
        self.assert_api_access(False)
    
    def test_login_backup_code(self):
        code = self.mfa_backup.data['backup_codes'][0]
        res = self.assert_mfa_login(self.mfa_backup)
        # Backup code invalidated
        self.mfa_backup.refresh_from_db()
        assert code not in self.mfa_backup.data['backup_codes']
    
    def test_login_backup_code_failure(self):
        self.assert_mfa_login(self.mfa_backup, data={'code': 'invalid'}, success=False)

    def test_login_totp(self):
        self.assert_mfa_login(self.mfa_totp)

    def test_login_totp_failure(self):
        self.assert_mfa_login(self.mfa_totp, data={'code': 'invalid'}, success=False)

    def test_login_mfa_method_of_other_user(self):
        other_user = create_user()
        other_mfa = MFAMethod.objects.create_totp(user=other_user)
        self.assert_mfa_login(user=self.user_mfa, mfa_method=other_mfa, success=False)

    @override_settings(REMOTE_USER_AUTH_ENABLED=True, REMOTE_USER_AUTH_HEADER='Remote-User')
    def test_login_remoteuser(self):
        AuthIdentity.objects.create(user=self.user_mfa, provider=AuthIdentity.PROVIDER_REMOTE_USER, identifier='remoteuser@example.com')
        res = self.client.post(reverse('auth-login-remoteuser'), HTTP_REMOTE_USER='remoteuser@example.com')
        assert res.status_code == 200
        assert res.data['status'] == 'success'
        self.assert_api_access(True)

    @override_settings(REMOTE_USER_AUTH_ENABLED=True, REMOTE_USER_AUTH_HEADER='Remote-User')
    def test_login_remoteuser_failure(self):
        AuthIdentity.objects.create(user=self.user_mfa, provider=AuthIdentity.PROVIDER_REMOTE_USER, identifier='remoteuser@example.com')
        res_no_header = self.client.post(reverse('auth-login-remoteuser'))
        assert res_no_header.status_code == 403
        self.assert_api_access(False)

        self.client.headers = {'Remote-User': 'other'}
        res_no_identity = self.client.post(reverse('auth-login-remoteuser'), HTTP_REMOTE_USER='unknown')
        assert res_no_identity.status_code == 403
        self.assert_api_access(False)

    @override_settings(LOCAL_USER_AUTH_ENABLED=False)
    def test_local_login_disabled(self):
        self.assert_login(self.user, success=False)
        self.assert_api_access(False)


@pytest.mark.django_db
class TestMfaMethodRegistration:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.password = 'Password1!'
        self.user = create_user(username='user', password=self.password)
        self.client = api_client()
        self.client.post(reverse('auth-login'), data={'username': self.user.username, 'password': self.password})
        self.client.post(reverse('auth-login'), data={'username': self.user.username, 'password': self.password})

    def test_register_backup_codes(self):
        res_begin = self.client.post(reverse('mfamethod-register-backup-begin', kwargs={'pentestuser_pk': 'self'}))
        assert res_begin.status_code == 200
        res_complete = self.client.post(reverse('mfamethod-register-backup-complete', kwargs={'pentestuser_pk': 'self'}))
        assert res_complete.status_code == 201
        assert self.user.mfa_methods.count() == 1
        mfa = self.user.mfa_methods.first()
        assert mfa.method_type == MFAMethodType.BACKUP
        assert mfa.data['backup_codes'] == res_begin.data['backup_codes']

    def test_register_totp(self):
        res_begin = self.client.post(reverse('mfamethod-register-totp-begin', kwargs={'pentestuser_pk': 'self'}))
        assert res_begin.status_code == 200
        data_begin = omit_keys(res_begin.data, ['qrcode'])
        res_complete = self.client.post(reverse('mfamethod-register-totp-complete', kwargs={'pentestuser_pk': 'self'}), data={
            'code': pyotp.TOTP(**data_begin).now(),
        })
        assert res_complete.status_code == 201
        assert self.user.mfa_methods.count() == 1
        mfa = self.user.mfa_methods.first()
        assert mfa.method_type == MFAMethodType.TOTP
        assert mfa.data == data_begin

    def test_reauthentication_timeout(self):
        # Simple login
        self.client.logout()
        self.client.post(reverse('auth-login'), data={'username': self.user.username, 'password': self.password})
        res1 = self.client.post(reverse('mfamethod-register-backup-begin', kwargs={'pentestuser_pk': 'self'}))
        assert res1.status_code == 403

        # Re-authentication
        self.client.post(reverse('auth-login'), data={'username': self.user.username, 'password': self.password})
        res2 = self.client.post(reverse('mfamethod-register-backup-begin', kwargs={'pentestuser_pk': 'self'}))
        assert res2.status_code == 200

        # Re-authentication timed out
        with mock_time(after=settings.SENSITIVE_OPERATION_REAUTHENTICATION_TIMEOUT * 2):
            res3 = self.client.post(reverse('mfamethod-register-backup-begin', kwargs={'pentestuser_pk': 'self'}))
            assert res3.status_code == 403


@pytest.mark.django_db
class TestEnableAdminPermissions:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.project_not_member = create_project()

        self.password = 'Password1!'
        self.user = create_user(is_superuser=True, password=self.password)
        self.client = api_client()
        self.client.post(reverse('auth-login'), data={'username': self.user.username, 'password': self.password})

    def has_admin_access(self):
        return self.client.get(reverse('pentestproject-detail', kwargs={'pk': self.project_not_member.pk})).status_code == 200
    
    def test_enable_admin_permissions(self):
        assert not self.has_admin_access()

        # Try without re-auth
        res_privesc_failed = self.client.post(reverse('pentestuser-enable-admin-permissions'))
        assert res_privesc_failed.status_code == 403
        assert res_privesc_failed.json()['code'] == 'reauth-required'

        # Re-authenticate
        old_session_id = self.client.session.session_key
        res_reauth = self.client.post(reverse('auth-login'), data={'username': self.user.username, 'password': self.password})
        assert res_reauth.status_code == 200
        assert self.client.session.session_key != old_session_id

        # Enable admin permissions
        res_privesc_success = self.client.post(reverse('pentestuser-enable-admin-permissions'))
        assert res_privesc_success.status_code == 200
        user_data = res_privesc_success.json()
        assert user_data['id'] == str(self.user.id)
        assert user_data['is_superuser']
        assert 'admin' in user_data['scope']
        assert self.client.session['admin_permissions_enabled']

        assert self.has_admin_access()

    def test_disable_admin_permissions(self):
        session = self.client.session
        session['admin_permissions_enabled'] = True
        session.save()

        assert self.has_admin_access()

        res = self.client.post(reverse('pentestuser-disable-admin-permissions'))
        assert res.status_code == 200
        user_data = res.json()
        assert user_data['id'] == str(self.user.id)
        assert user_data['is_superuser']
        assert 'admin' not in user_data['scope']
        assert not self.client.session.get('admin_permissions_enabled')

        assert not self.has_admin_access()
        
