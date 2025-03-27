import io
import re
from datetime import datetime, timedelta
from unittest import mock
from urllib.parse import parse_qsl
from uuid import uuid4

import pyotp
import pytest
from asgiref.sync import async_to_sync
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string

from sysreptor.management.commands import createapitoken
from sysreptor.tests.mock import (
    api_client,
    create_project,
    create_user,
    mock_time,
    override_configuration,
    update,
)
from sysreptor.tests.utils import assertKeysEqual
from sysreptor.users.models import APIToken, AuthIdentity, MFAMethod, MFAMethodType, PentestUser
from sysreptor.utils import utils
from sysreptor.utils.utils import omit_keys


@pytest.mark.django_db()
class TestLogin:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.password = get_random_string(32)
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

    def assert_mfa_login(self, mfa_method, data=None, user=None, success=True, status='success'):
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
            assert res.data['status'] == status
            if status == 'success':
                self.assert_api_access(True)
        else:
            assert res.status_code in [400, 403]
            self.assert_api_access(False)
        return res

    def assert_change_password(self, password=None, success=True):
        res = self.client.post(reverse('auth-change-password'), data={'password': password or get_random_string(32)})
        if success:
            assert res.status_code == 200
            assert res.data['status'] == 'success'
        else:
            assert res.status_code in [400, 403]
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
        self.assert_login(user=self.user, password='invalid_password', success=False)  # noqa: S106

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
        self.assert_mfa_login(self.mfa_backup)
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

    def test_must_change_password(self):
        update(self.user, must_change_password=True)

        self.assert_login(self.user, status='password-change-required')
        self.assert_api_access(False)
        self.assert_change_password(password=get_random_string(3), success=False)
        self.assert_api_access(False)
        self.assert_change_password()
        self.assert_api_access(True)

        self.user.refresh_from_db()
        assert not self.user.must_change_password

    def test_must_change_password_mfa(self):
        update(self.user_mfa, must_change_password=True)

        self.assert_mfa_login(mfa_method=self.mfa_totp, user=self.user_mfa, status='password-change-required')
        self.assert_api_access(False)
        self.assert_change_password()
        self.assert_api_access(True)

        self.user.refresh_from_db()
        assert not self.user.must_change_password

    @override_configuration(REMOTE_USER_AUTH_ENABLED=True, REMOTE_USER_AUTH_HEADER='Remote-User')
    def test_login_remoteuser(self):
        AuthIdentity.objects.create(user=self.user_mfa, provider=AuthIdentity.PROVIDER_REMOTE_USER, identifier='remoteuser@example.com')
        res = self.client.post(reverse('auth-login-remoteuser'), HTTP_REMOTE_USER='remoteuser@example.com')
        assert res.status_code == 200
        assert res.data['status'] == 'success'
        self.assert_api_access(True)

    @override_configuration(REMOTE_USER_AUTH_ENABLED=True, REMOTE_USER_AUTH_HEADER='Remote-User')
    def test_login_remoteuser_failure(self):
        AuthIdentity.objects.create(user=self.user_mfa, provider=AuthIdentity.PROVIDER_REMOTE_USER, identifier='remoteuser@example.com')
        res_no_header = self.client.post(reverse('auth-login-remoteuser'))
        assert res_no_header.status_code == 403
        self.assert_api_access(False)

        self.client.headers = {'Remote-User': 'other'}
        res_no_identity = self.client.post(reverse('auth-login-remoteuser'), HTTP_REMOTE_USER='unknown')
        assert res_no_identity.status_code == 403
        self.assert_api_access(False)

    @override_configuration(LOCAL_USER_AUTH_ENABLED=False)
    def test_local_login_disabled(self):
        self.assert_login(self.user, success=False)
        self.assert_api_access(False)


@pytest.mark.django_db()
class TestMfaMethodRegistration:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.password = get_random_string(32)
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


@pytest.mark.django_db()
class TestEnableAdminPermissions:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.project_not_member = create_project()

        self.password = get_random_string(32)
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


@pytest.mark.django_db()
class TestAPITokenAuth:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user(is_superuser=True)
        self.api_token = APIToken.objects.create(user=self.user)
        self.client = api_client()

    def assert_api_access(self, url, expected, api_token=None):
        res = self.client.get(url, HTTP_AUTHORIZATION='Bearer ' + (api_token or self.api_token.token_formatted))
        assert (res.status_code == 200) == expected
        return res

    def test_api_token_auth(self):
        res = self.assert_api_access(reverse('pentestuser-detail', kwargs={'pk': 'self'}), True)
        assert res.data['id'] == str(self.user.id)

    def test_createapitoken_command(self):
        stdout = io.StringIO()
        call_command(createapitoken.Command(stdout=stdout), self.user.username)
        self.assert_api_access(reverse('pentestuser-detail', kwargs={'pk': 'self'}), True, api_token=stdout.getvalue().strip())

    def test_update_last_used_date(self):
        assert self.api_token.last_used is None
        self.assert_api_access(reverse('pentestuser-detail', kwargs={'pk': 'self'}), True)
        self.api_token.refresh_from_db()
        assert self.api_token.last_used.date() == timezone.now().date()

    def test_full_admin_permissions_without_reauth(self):
        project_not_member = create_project()
        self.assert_api_access(reverse('pentestproject-detail', kwargs={'pk': project_not_member.pk}), True)

    def test_user_inactive(self):
        update(self.user, is_active=False)
        self.assert_api_access(reverse('pentestuser-detail', kwargs={'pk': 'self'}), False)

    def test_token_expired(self):
        update(self.api_token, expire_date=(timezone.now() - timedelta(days=10)).date())
        self.assert_api_access(reverse('pentestuser-detail', kwargs={'pk': 'self'}), False)


@pytest.mark.django_db()
class TestForgotPassword:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user(username='user', email='user@example.com')
        self.token_user = default_token_generator.make_token(self.user)
        self.client = api_client()

    def test_forgot_password_flow(self):
        res1 = self.client.post(reverse('auth-forgot-password-send'), data={'email': self.user.email})
        assert res1.status_code == 200
        assert len(mail.outbox) == 1
        token_data = dict(parse_qsl(re.search(r'/login/set-password/\?(?P<params>.*)', mail.outbox[0].body).group('params')))

        res2 = self.client.post(reverse('auth-forgot-password-check'), data=token_data)
        assert res2.status_code == 200
        assert res2.data['id'] == str(self.user.id)
        assertKeysEqual(res2.data, self.user, ['username', 'name', 'email'])

        new_password = get_random_string(32)
        res3 = self.client.post(reverse('auth-forgot-password-reset'), data=token_data | {'password': new_password})
        assert res3.status_code == 200
        self.user.refresh_from_db()
        assert self.user.check_password(new_password)

    @pytest.mark.parametrize(('expected', 'get_email'), [
        (True, lambda s: s.user.email),
        (False, lambda s: 'nonexistent@example.com'),
        (False, lambda s: update(s.user, is_active=False).email),
    ])
    def test_email_sent(self, expected, get_email):
        res = self.client.post(reverse('auth-forgot-password-send'), data={'email': get_email(self)})
        assert res.status_code in ([200] if expected else [200, 403])
        assert len(mail.outbox) == (1 if expected else 0)

    @pytest.mark.parametrize(('expected', 'settings'), [
        (True, {}),
        (False, {'FORGOT_PASSWORD_ENABLED': False}),
        (False, {'LOCAL_USER_AUTH_ENABLED': False}),
        (False, {'EMAIL_HOST': None}),
    ])
    def test_email_sent_settings(self, expected, settings):
        with override_settings(**settings), override_configuration(**settings):
            self.test_email_sent(expected, lambda s: s.user.email)

    @pytest.mark.parametrize(('expected', 'get_user', 'get_token'), [
        (True, lambda s: s.user, lambda s: s.token_user),
        (False, lambda s: update(s.user, is_active=False), lambda s: s.token_user),
        (False, lambda s: create_user(email='other@example.com'), lambda s: s.token_user),
        (False, lambda s: PentestUser(id=uuid4()), lambda s: s.token_user),
        (False, lambda s: s.user, lambda s: 'invalid token'),
    ])
    def test_check_token(self, expected, get_user, get_token):
        token_data = {
            'user': get_user(self).id,
            'token': get_token(self),
        }
        res1 = self.client.post(reverse('auth-forgot-password-check'), data=token_data)
        assert res1.status_code in ([200] if expected else [400, 403])

        res2 = self.client.post(reverse('auth-forgot-password-reset'), data=token_data | {'password': get_random_string(32)})
        assert res2.status_code in ([200] if expected else [400, 403])

    def test_check_token_expired(self):
        with mock.patch.object(default_token_generator, '_now', return_value=datetime.now() + timedelta(seconds=settings.PASSWORD_RESET_TIMEOUT * 2)):
            self.test_check_token(False, lambda s: s.user, lambda s: s.token_user)

    @pytest.mark.parametrize(('expected', 'settings'), [
        (True, {}),
        (False, {'FORGOT_PASSWORD_ENABLED': False}),
        (False, {'LOCAL_USER_AUTH_ENABLED': False}),
        (False, {'EMAIL_HOST': None}),
    ])
    def test_check_token_settings(self, expected, settings):
        with override_settings(**settings), override_configuration(**settings):
            self.test_check_token(expected, lambda s: s.user, lambda s: s.token_user)
