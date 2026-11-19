import io
import itertools
import re
from datetime import datetime, timedelta
from unittest import mock
from urllib.parse import parse_qsl
from uuid import uuid4

import pyotp
import pytest
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.management import call_command
from django.test import RequestFactory, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string

from sysreptor.management.commands import createapitoken
from sysreptor.tests.mock import (
    api_client,
    api_client_with_token,
    create_api_token,
    create_project,
    create_project_type,
    create_session,
    create_template,
    create_user,
    mock_time,
    override_configuration,
    update,
)
from sysreptor.tests.utils import assertKeysEqual
from sysreptor.users.auth import APITokenAuthentication
from sysreptor.users.models import APIToken, AuthIdentity, MFAMethod, MFAMethodType, PentestUser, Session
from sysreptor.users.roles import Permission
from sysreptor.users.serializers import LEGACY_USER_FLAG_ROLES, PentestUserDetailSerializer
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

    def mfa_login_request(self, mfa_method, data=None):
        if mfa_method.method_type == MFAMethodType.BACKUP:
            return self.client.post(reverse('auth-login-code'), data={
                'id': str(mfa_method.id),
                'code': mfa_method.data['backup_codes'][0],
            } | (data or {}))
        elif mfa_method.method_type == MFAMethodType.TOTP:
            res = self.client.post(reverse('auth-login-code'), data={
                'id': str(mfa_method.id),
                'code': pyotp.TOTP(**mfa_method.data).now(),
            } | (data or {}))
            return res
        elif mfa_method.method_type == MFAMethodType.FIDO2:
            raise NotImplementedError('FIDO2 login is not supported in tests')

    def assert_mfa_login(self, mfa_method, data=None, user=None, success=True, status='success'):
        self.assert_login(user=user or self.user_mfa, status='mfa-required')
        res = self.mfa_login_request(mfa_method, data)

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

    def test_login_username_whitespace_not_trimmed(self):
        res = self.client.post(reverse('auth-login'), data={
            'username': f' {self.user.username} ',
            'password': self.password,
        })
        assert res.status_code == 400
        self.assert_api_access(False)

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

    @override_settings(MFA_MAX_FAILED_ATTEMPTS=1)
    def test_failed_mfa_locks_user(self):
        # Invalid password: don't count as failed MFA attempt
        self.assert_login(user=self.user_mfa, password='invalid_password', success=False)  # noqa: S106
        self.user_mfa.refresh_from_db()
        assert self.user_mfa.failed_mfa_attempts == 0

        # Failed MFA limit reached: lock user
        self.assert_login(user=self.user_mfa, status='mfa-required')
        assert self.mfa_login_request(self.mfa_totp, data={'code': 'invalid'}).status_code == 400
        self.user_mfa.refresh_from_db()
        assert self.user_mfa.failed_mfa_attempts == 1
        assert not self.user_mfa.is_active

        # User can not login anymore
        # via the same MFA method
        assert self.mfa_login_request(self.mfa_totp).status_code == 400
        # vai another MFA method
        assert self.mfa_login_request(self.mfa_backup).status_code == 400
        # via a fresh password login
        self.assert_login(user=self.user_mfa, success=False)  # noqa: S106

        # Re-activate user: reset failed MFA attempts
        update(self.user_mfa, is_active=True)
        self.user_mfa.refresh_from_db()
        self.assert_mfa_login(self.mfa_totp, success=True)

    def test_mfa_failed_attempts_reset_on_success(self):
        update(self.user_mfa, failed_mfa_attempts=5)
        self.assert_mfa_login(self.mfa_totp)
        self.user_mfa.refresh_from_db()
        assert self.user_mfa.failed_mfa_attempts == 0

    def test_login_inactive_user_wrong_password(self):
        update(self.user_mfa, is_active=False)

        res = self.assert_login(user=self.user_mfa, success=False)  # noqa: S106
        assert 'user is disabled' in str(res.data).lower()

        res = self.assert_login(user=self.user_mfa, password='invalid_password', success=False)  # noqa: S106
        assert 'user is disabled' not in str(res.data).lower()
        assert 'invalid username or password' in str(res.data).lower()

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

    def test_local_login_disabled_user(self):
        update(self.user, can_login_local=False)
        self.assert_login(self.user, success=False)


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
        assert user_data['is_admin']
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
        assert not user_data['is_admin']
        assert not self.client.session.get('admin_permissions_enabled')

        assert not self.has_admin_access()


@pytest.mark.django_db()
class TestAPITokenAuth:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user(is_superuser=True)
        self.api_token = APIToken.objects.create(user=self.user, admin_permissions_enabled=True)
        self.client = api_client()

    def assert_api_access(self, url, expected, api_token=None):
        res = api_client_with_token(api_token or self.api_token).get(url)
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

    def test_admin_permissions_disabled(self):
        update(self.api_token, admin_permissions_enabled=False)
        project_not_member = create_project()
        self.assert_api_access(reverse('pentestproject-detail', kwargs={'pk': project_not_member.pk}), False)

    def test_user_inactive(self):
        update(self.user, is_active=False)
        self.assert_api_access(reverse('pentestuser-detail', kwargs={'pk': 'self'}), False)

    def test_token_expired(self):
        update(self.api_token, expire_date=(timezone.now() - timedelta(days=10)).date())
        self.assert_api_access(reverse('pentestuser-detail', kwargs={'pk': 'self'}), False)


@pytest.mark.django_db()
class TestAPITokenCreate:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.password = get_random_string(32)
        self.user = create_user(is_superuser=True, password=self.password)
        self.client = api_client()
        self.client.post(reverse('auth-login'), data={'username': self.user.username, 'password': self.password})
        # Re-auth for sensitive operation
        self.client.post(reverse('auth-login'), data={'username': self.user.username, 'password': self.password})

    def create_token(self, admin_permissions_enabled=False):
        return self.client.post(reverse('apitoken-list', kwargs={'pentestuser_pk': 'self'}), data={
            'name': 'Test Token',
            'admin_permissions_enabled': admin_permissions_enabled,
        })

    def test_create_with_admin_permissions_as_admin(self):
        session = self.client.session
        session['admin_permissions_enabled'] = True
        session.save()

        res = self.create_token(admin_permissions_enabled=True)
        assert res.status_code == 201
        assert res.data['admin_permissions_enabled'] is True
        assert APIToken.objects.get(id=res.data['id']).admin_permissions_enabled is True

    def test_create_with_admin_permissions_without_admin_mode(self):
        res = self.create_token(admin_permissions_enabled=True)
        assert res.status_code == 400
        assert 'admin_permissions_enabled' in res.data

    def test_create_without_admin_permissions(self):
        res = self.create_token(admin_permissions_enabled=False)
        assert res.status_code == 201
        assert res.data['admin_permissions_enabled'] is False

    def test_create_with_admin_permissions_as_non_superuser(self):
        user = create_user(password=self.password)
        client = api_client()
        client.post(reverse('auth-login'), data={'username': user.username, 'password': self.password})
        client.post(reverse('auth-login'), data={'username': user.username, 'password': self.password})

        res = client.post(reverse('apitoken-list', kwargs={'pentestuser_pk': 'self'}), data={
            'name': 'Test Token',
            'admin_permissions_enabled': True,
        })
        assert res.status_code == 400
        assert 'admin_permissions_enabled' in res.data

    def test_prevent_update(self):
        token = APIToken.objects.create(user=self.user)
        res = self.client.patch(reverse('apitoken-detail', kwargs={'pentestuser_pk': 'self', 'pk': token.id}), data={
            'name': 'Test Token',
            'admin_permissions_enabled': True,
        })
        assert res.status_code == 405


@pytest.mark.django_db()
class TestRestrictedApiToken:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user(
            mfa=True, apitoken=True, public_key=True,
            roles=['regular_user', 'template_editor', 'designer', 'project_admin'],
        )
        AuthIdentity.objects.create(user=self.user, provider='dummy', identifier='user@example.com')
        self.project = create_project(members=[self.user])
        self.template = create_template()
        self.project_type = create_project_type()
        self.token = create_api_token(
            self.user,
            projects=[self.project],
            permissions=[Permission.PROJECT_READ, Permission.PROJECT_EDIT_CONTENT, Permission.PROJECT_EXPORT],
        )
        self.client_token = api_client_with_token(self.token)

    def test_allowed_project_access_and_read_only_write_denied(self):
        assert self.client_token.get(reverse('pentestproject-detail', kwargs={'pk': self.project.id})).status_code == 200
        finding = self.project.findings.first()
        finding_url = reverse('finding-detail', kwargs={'project_pk': self.project.id, 'id': finding.finding_id})
        assert self.client_token.patch(finding_url, data={'data': {'title': 'changed'}}).status_code == 200

        ro_client = api_client_with_token(create_api_token(self.user, projects=[self.project], permissions=[Permission.PROJECT_READ]))
        assert ro_client.patch(finding_url, data={'data': {'title': 'changed'}}).status_code == 403

    def test_cross_project_access_denied(self):
        other = create_project(members=[self.user])
        create_project(members=[])

        res_projects = self.client_token.get(reverse('pentestproject-list'))
        assert [p['id'] for p in res_projects.data['results']] == [str(self.project.id)]
        assert self.client_token.get(reverse('finding-detail', kwargs={
            'project_pk': other.id,
            'id': other.findings.first().finding_id,
        })).status_code == 404
        assert self.client_token.post(
            reverse('pentestproject-export-bulk'),
            {'ids': [str(self.project.id), str(other.id)]},
        ).status_code in (400, 403)

    def test_member_removed_from_project(self):
        self.project.members.all().delete()
        assert self.client_token.get(reverse('pentestproject-detail', kwargs={'pk': self.project.id})).status_code == 404

    def test_admin_permissions_dropped_from_user(self):
        update(self.user, roles=['regular_user', 'project_admin'], is_superuser=True)
        self.user.admin_permissions_enabled = True
        self.project.members.all().delete()
        assert self.client_token.get(reverse('pentestproject-detail', kwargs={'pk': self.project.id})).status_code == 404

    def test_delete_last_project_does_not_unrestrict(self):
        self.project.delete()
        self.token.refresh_from_db()
        assert self.token.projects  # stale UUID remains
        p = create_project(members=[self.user])
        assert self.client_token.get(reverse('pentestproject-detail', kwargs={'pk': p.id})).status_code == 404

    def test_empty_projects_list_sees_nothing(self):
        client = api_client_with_token(create_api_token(self.user, projects=[], permissions=[Permission.PROJECT_READ]))
        assert client.get(reverse('pentestproject-list')).data['results'] == []

    @override_configuration(ENABLE_PRIVATE_DESIGNS=True)
    def test_personal_and_private_resources_denied(self):
        pt_private = create_project_type(linked_user=self.user)
        res = self.client_token.get(reverse('projecttype-list'))
        assert str(pt_private.id) not in [d['id'] for d in res.data['results']]
        assert self.client_token.get(reverse('projecttype-detail', kwargs={'pk': pt_private.id})).status_code == 404
        assert self.client_token.post(reverse('projecttype-list'), data={
            'name': 'Private via token',
            'scope': 'private',
            'language': 'en-US',
        }).status_code in (400, 403)

        self_kwargs = {'pentestuser_pk': 'self'}
        assert self.client_token.get(reverse('usernotebookpage-list', kwargs=self_kwargs)).status_code == 403
        assert self.client_token.get(reverse('notification-list', kwargs=self_kwargs)).status_code == 403
        assert self.client_token.get(reverse('mfamethod-list', kwargs=self_kwargs)).status_code == 403
        assert self.client_token.get(reverse('apitoken-list', kwargs=self_kwargs)).status_code == 403
        assert self.client_token.get(reverse('authidentity-list', kwargs=self_kwargs)).status_code == 403
        assert self.client_token.get(reverse('userpublickey-list', kwargs=self_kwargs)).status_code == 403

    def test_self_read_allowed_write_denied(self):
        assert self.client_token.get(reverse('pentestuser-detail', kwargs={'pk': 'self'})).status_code == 200
        assert self.client_token.patch(reverse('pentestuser-detail', kwargs={'pk': 'self'}), data={'first_name': 'X'}).status_code == 403

    @pytest.mark.parametrize(('permissions', 'projects', 'expectations'), [
        ([Permission.PROJECT_READ], 'member', {'project_detail': 200, 'finding_write': 403, 'project_export': 403, 'template_detail': 403, 'design_detail': 404}),
        ([Permission.PROJECT_READ, Permission.PROJECT_EDIT_CONTENT, Permission.PROJECT_EXPORT], 'member', {'project_detail': 200, 'finding_write': 200, 'project_export': 200, 'template_detail': 403, 'design_detail': 404}),
        ([Permission.PROJECT_READ, Permission.PROJECT_UPDATE_SETTINGS, Permission.DESIGN_GLOBAL_READ], 'member', {'project_detail': 200, 'finding_write': 403, 'project_settings': 200, 'template_detail': 403, 'design_detail': 200}),
        ([Permission.TEMPLATE_READ], None, {'project_detail': 403, 'project_list_empty': True, 'template_detail': 200, 'design_detail': 404}),
        ([Permission.TEMPLATE_READ, Permission.TEMPLATE_EDIT, Permission.DESIGN_GLOBAL_READ], None, {'project_detail': 403, 'template_detail': 200, 'template_write': 200, 'design_detail': 200}),
        ([], None, {'project_detail': 403, 'project_list_empty': True, 'template_detail': 403, 'template_list_empty': True, 'design_detail': 404, 'self_detail': 200}),
    ])
    def test_permission_allowlist(self, permissions, projects, expectations):
        client = api_client_with_token(create_api_token(
            self.user,
            permissions=permissions,
            projects=[self.project] if projects is not None else None,
        ))
        finding = self.project.findings.first()

        if 'project_detail' in expectations:
            assert client.get(reverse('pentestproject-detail', kwargs={'pk': self.project.id})).status_code == expectations['project_detail']
        if expectations.get('project_list_empty'):
            assert client.get(reverse('pentestproject-list')).data['results'] == []
        if 'finding_write' in expectations:
            assert client.patch(
                reverse('finding-detail', kwargs={'project_pk': self.project.id, 'id': finding.finding_id}),
                data={'data': {'title': 'changed'}},
            ).status_code == expectations['finding_write']
        if 'project_export' in expectations:
            assert client.post(reverse('pentestproject-export', kwargs={'pk': self.project.id})).status_code == expectations['project_export']
        if 'project_settings' in expectations:
            assert client.patch(
                reverse('pentestproject-detail', kwargs={'pk': self.project.id}),
                data={'name': 'Renamed'},
            ).status_code == expectations['project_settings']
        if 'template_detail' in expectations:
            assert client.get(reverse('findingtemplate-detail', kwargs={'pk': self.template.id})).status_code == expectations['template_detail']
        if expectations.get('template_list_empty'):
            assert client.get(reverse('findingtemplate-list')).data['results'] == []
        if 'template_write' in expectations:
            assert client.patch(
                reverse('findingtemplate-detail', kwargs={'pk': self.template.id}),
                data=client.get(reverse('findingtemplate-detail', kwargs={'pk': self.template.id})).data,
            ).status_code == expectations['template_write']
        if 'design_detail' in expectations:
            assert client.get(reverse('projecttype-detail', kwargs={'pk': self.project_type.id})).status_code == expectations['design_detail']
        if 'self_detail' in expectations:
            assert client.get(reverse('pentestuser-detail', kwargs={'pk': 'self'})).status_code == expectations['self_detail']

    def _authenticate_restricted_token(self, token):
        request = RequestFactory().get('/')
        request.META['HTTP_AUTHORIZATION'] = f'Bearer {token.token_formatted}'
        class _View:
            allow_restricted_api_token = True
        request.parser_context = {'view': _View()}
        user, _ = APITokenAuthentication().authenticate(request)
        return user

    def test_admin_permissions_restricted(self):
        update(self.user, is_superuser=True, admin_permissions_enabled=True, roles=['regular_user', 'project_admin'])
        token = create_api_token(
            self.user,
            projects=[self.project],
            permissions=[Permission.PROJECT_READ, Permission.ADMIN_ACCESS_ALL_PROJECTS],
        )
        user = self._authenticate_restricted_token(token)
        assert not user.is_admin
        assert user.is_superuser
        assert set(user.effective_permissions) == {Permission.PROJECT_READ}
        assert not user.has_permission(Permission.ADMIN_ACCESS_ALL_PROJECTS)

    def test_permissions_cannot_exceed_user_roles(self):
        update(self.user, roles=['regular_user'])
        token = create_api_token(
            self.user,
            permissions=[
                Permission.PROJECT_READ,
                Permission.TEMPLATE_EDIT,  # requires template_editor
                Permission.DESIGN_GLOBAL_EDIT,  # requires designer
                Permission.USER_EDIT,  # requires user_manager
            ],
        )
        user = self._authenticate_restricted_token(token)
        assert set(user.effective_permissions) == {Permission.PROJECT_READ}
        assert not user.has_permission(Permission.TEMPLATE_EDIT)
        assert not user.has_permission(Permission.DESIGN_GLOBAL_EDIT)
        assert not user.has_permission(Permission.USER_EDIT)

    @pytest.mark.parametrize(('expected', 'data'), [
        (True, {}),
        (True, {'permissions': None, 'projects': None}),
        (True, {'permissions': [Permission.PROJECT_READ], 'projects': None}),
        (True, {'permissions': [], 'projects': None}),
        (True, {'admin_permissions_enabled': True}),
        (False, {'projects': [], 'permissions': None}),  # projects without permissions
        (False, {'projects': ['member']}),  # omitted permissions — no API default
        (True, {'projects': [], 'permissions': [Permission.PROJECT_READ]}),
        (True, {'projects': ['member'], 'permissions': [Permission.PROJECT_READ, Permission.PROJECT_EXPORT]}),
        (True, {'projects': ['member'], 'permissions': [Permission.PROJECT_READ, Permission.PROJECT_EDIT_CONTENT]}),
        (True, {'projects': ['member'], 'permissions': [Permission.PROJECT_READ, Permission.PROJECT_CREATE]}),
        (False, {'projects': ['other'], 'permissions': [Permission.PROJECT_READ]}),
        (False, {'projects': ['member'], 'permissions': [Permission.PROJECT_READ], 'admin_permissions_enabled': True}),
        (False, {'projects': ['member'], 'permissions': [Permission.PROJECT_CREATE]}),  # missing project.read
        (False, {'projects': ['member'], 'permissions': [Permission.PROJECT_EXPORT]}),  # missing project.read
        (False, {'projects': ['member'], 'permissions': [Permission.ADMIN_ACCESS_ALL_PROJECTS]}),
        (False, {'projects': ['member'], 'permissions': [Permission.PROJECT_READ, Permission.ADMIN_ACCESS_ALL_PROJECTS]}),
    ])
    def test_create_project_token_validation(self, expected, data):
        projects = {
            'member': create_project(members=[self.user]),
            'other': create_project(members=[]),
        }
        update(self.user, is_superuser=True, admin_permissions_enabled=True)
        client = api_client(self.user)
        session = client.session
        session['authentication_info'] = {
            'login_time': timezone.now().isoformat(),
            'reauth_time': timezone.now().isoformat(),
        }
        session.save()
        body = {
            'name': 'test',
            **{k: v for k, v in data.items() if k not in ('projects', 'permissions')},
        }
        if 'projects' in data:
            body['projects'] = (
                None if data['projects'] is None
                else [{'id': str(projects[p].id)} for p in data['projects']]
            )
        if 'permissions' in data:
            body['permissions'] = (
                None if data['permissions'] is None
                else [getattr(p, 'value', p) for p in data['permissions']]
            )
        res = client.post(reverse('apitoken-list', kwargs={'pentestuser_pk': 'self'}), data=body)
        assert res.status_code == (201 if expected else 400), res.data


@pytest.mark.django_db(transaction=True)
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
        token_data = dict(parse_qsl(re.search(r'/login/set-password/#(?P<params>.*)', mail.outbox[0].body).group('params')))

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


@pytest.mark.django_db()
class TestPasswordChangeSessionRevocation:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.password = get_random_string(32)
        self.user = create_user(password=self.password, email='user@example.com')

    def create_user_session(self):
        session = create_session(self.user)
        session['authentication_info'] = {'reauth_time': timezone.now().isoformat()}
        session.save()
        return session

    def session_client(self, session=None):
        session = session or self.create_user_session()
        client = api_client()
        client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key
        return client

    def test_change_password_keeps_current_revokes_others(self):
        client = self.session_client()
        other = self.create_user_session()

        assert client.post(reverse('pentestuser-change-password'), data={'password': get_random_string(32)}).status_code == 200
        assert client.get(reverse('pentestuser-self')).status_code == 200
        assert Session.objects.filter(user=self.user).count() == 1
        assert not Session.objects.filter(session_key=other.session_key).exists()

    @pytest.mark.parametrize('action', [
        'admin_reset',
        'forgot_password',
    ])
    def test_password_reset_revokes_all_sessions(self, action):
        self.create_user_session()
        self.create_user_session()

        if action == 'admin_reset':
            res = api_client(create_user(roles=['regular_user', 'user_manager'])).post(
                reverse('pentestuser-reset-password', kwargs={'pk': self.user.id}),
                data={'password': get_random_string(32)},
            )
        else:
            res = api_client().post(reverse('auth-forgot-password-reset'), data={
                'user': self.user.id,
                'token': default_token_generator.make_token(self.user),
                'password': get_random_string(32),
            })

        assert res.status_code == 200
        assert not Session.objects.filter(user=self.user).exists()

    def test_must_change_password_revokes_other_sessions(self):
        other = self.create_user_session()
        update(self.user, must_change_password=True)
        client = api_client()

        assert client.post(reverse('auth-login'), data={'username': self.user.username, 'password': self.password}).data['status'] == 'password-change-required'
        assert client.post(reverse('auth-change-password'), data={'password': get_random_string(32)}).data['status'] == 'success'
        assert client.get(reverse('pentestuser-self')).status_code == 200
        assert not Session.objects.filter(session_key=other.session_key).exists()

    def test_deactivate_user_revokes_all_sessions(self):
        self.create_user_session()
        self.create_user_session()
        update(self.user, is_active=False)
        assert not Session.objects.filter(user=self.user).exists()


@pytest.mark.django_db()
class TestUserPermissionAssignment:
    protected_fields = set(PentestUserDetailSerializer.Meta.fields) - {
        # Exclude non-permission and read-only fields
        'id', 'created', 'updated', 'last_login',
        'name', 'title_before', 'first_name', 'middle_name', 'last_name', 'title_after',
        'phone', 'mobile', 'color', 'is_admin', 'effective_permissions', 'has_password', 'can_login_sso', 'is_mfa_enabled',
    }

    @pytest.fixture(autouse=True)
    def setUp(self):
        create_user(roles=['regular_user'], username='regular', is_superuser=False)
        create_user(roles=['regular_user', 'user_manager'], username='user_manager', is_superuser=False)
        create_user(roles=['regular_user'], username='superuser', is_superuser=True)
        create_user(username='other')

    @pytest.mark.parametrize(('username', 'data', 'expected'), [
        ('regular', {}, False),
        ('superuser', {}, True),
        ('superuser', {'is_superuser': True, 'roles': ['regular_user', 'user_manager'], 'email': 'newuser@example.com'}, True),
        ('user_manager', {}, True),
        ('user_manager', {'is_superuser': False, 'roles': ['regular_user', 'user_manager', 'designer', 'template_editor', 'global_archiver', 'project_admin'], 'email': 'newuser@example.com'}, True),        ('user_manager', {'is_superuser': True}, False),
    ])
    def test_create_user(self, username, data, expected):
        user_req = PentestUser.objects.get(username=username)
        user_req.admin_permissions_enabled = True

        res = api_client(user_req).post(reverse('pentestuser-list'), data={
            'username': 'new',
            'email': 'new@example.com',
            'password': get_random_string(32),
        } | data)
        assert res.status_code in ([201] if expected else [201, 403])
        user_new = PentestUser.objects.filter(username='new').first()
        if user_new:
            for k, v in data.items():
                assert (res.data[k] == v) is expected
                assert (getattr(user_new, k) == v) is expected

    @staticmethod
    def get_test_update_params(username, usernames_target, fields, expected):
        return sorted(itertools.chain(*[[(username, username_target, f, expected) for f in fields] for username_target in usernames_target]))

    @staticmethod
    def get_field_value(user, field):
        if role := LEGACY_USER_FLAG_ROLES.get(field):
            return role in (user.roles or [])
        return getattr(user, field)

    @pytest.mark.parametrize(('username', 'username_target', 'field', 'expected'), [
        *get_test_update_params('regular', ['self', 'other'], protected_fields, False),
        *get_test_update_params('user_manager', ['self', 'other'], protected_fields - {'is_superuser', 'is_system_user', 'is_active', *LEGACY_USER_FLAG_ROLES}, True),
        *get_test_update_params('user_manager', ['self', 'other'], LEGACY_USER_FLAG_ROLES, False),
        *get_test_update_params('user_manager', ['self', 'other', 'superuser'], ['is_superuser', 'is_system_user'], False),
        *get_test_update_params('user_manager', ['superuser'], protected_fields, False),
        *get_test_update_params('superuser', ['self', 'other', 'user_manager'], protected_fields - {'is_active', 'is_system_user', *LEGACY_USER_FLAG_ROLES}, True),
        *get_test_update_params('superuser', ['self', 'other', 'user_manager'], LEGACY_USER_FLAG_ROLES, False),
    ])
    def test_update_field(self, username, username_target, field, expected):
        user_req = PentestUser.objects.get(username=username)
        user_req.admin_permissions_enabled = True
        user_target = PentestUser.objects.get(username=username if username_target == 'self' else username_target)

        update_data = {
            'email': 'changed@example.com',
            'username': 'changed',
            'roles': ['regular_user', 'designer'],
        }
        if field in update_data:
            value = update_data[field]
        elif isinstance(v := self.get_field_value(user_target, field), bool):
            value = not v
        else:
            raise ValueError(f'Cannot automatically handle non-bool field {field}. Exclude field or add it to update_data above.')
        data = {field: value}
        original_data = {k: self.get_field_value(user_target, k) for k in data.keys()}

        res = api_client(user_req).patch(reverse('pentestuser-detail', kwargs={'pk': 'self' if user_req == user_target else user_target.id}), data=data)
        assert res.status_code in ([200] if expected else [200, 403])
        user_target.refresh_from_db()
        assert {k: self.get_field_value(user_target, k) for k in data.keys()} == (data if expected else original_data)
