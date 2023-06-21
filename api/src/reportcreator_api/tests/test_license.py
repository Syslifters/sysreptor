import json
import pytest
from uuid import uuid4
from django.test import override_settings
from Cryptodome.Signature import eddsa
from Cryptodome.PublicKey import ECC
from Cryptodome.Hash import SHA512
from base64 import b64decode, b64encode
from datetime import timedelta
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from unittest import mock
from rest_framework.test import APIClient
from rest_framework import status
from django.utils.crypto import get_random_string

from reportcreator_api.utils import license
from reportcreator_api.tests.mock import create_project, create_public_key, create_user, api_client


def assert_api_license_error(res):
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['code'] == 'license'


@pytest.mark.django_db
class TestCommunityLicenseRestrictions:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.password = get_random_string(length=32)
        self.user = create_user(is_superuser=True, password=self.password)
        self.user_regular = create_user(password=self.password)
        self.user_system = create_user(is_system_user=True, password=self.password)
        self.client = api_client(self.user)

        with mock.patch('reportcreator_api.utils.license.check_license', lambda: {'type': license.LicenseType.COMMUNITY, 'users': 2, 'error': None}):
            yield

    def test_spellcheck_disabled(self):
        assert self.client.get(reverse('utils-settings')).data['features']['spellcheck'] is False
        assert_api_license_error(self.client.post(reverse('utils-spellcheck')))
        assert_api_license_error(self.client.post(reverse('utils-spellcheck-words')))

    def test_admin_privesc_disabled(self):
        assert self.user.is_admin
        assert 'admin' in self.client.get(reverse('pentestuser-self')).data['scope']
        assert_api_license_error(self.client.post(reverse('pentestuser-disable-admin-permissions')))
        assert_api_license_error( self.client.post(reverse('pentestuser-enable-admin-permissions')))

    def test_backup_api_disabled(self):
        self.client.force_authenticate(self.user_system)
        assert_api_license_error(self.client.post(reverse('utils-backup'), data={'key': settings.BACKUP_KEY}))

    def test_archiving_disabled(self):
        public_key = create_public_key(user=self.user)
        project = create_project(members=[self.user])
        assert_api_license_error(self.client.post(reverse('userpublickey-list', kwargs={'pentestuser_pk': 'self'}), data={'name': 'test', 'public_key': public_key.public_key}))
        assert_api_license_error(self.client.post(reverse('pentestproject-archive', kwargs={'pk': project.pk})))

    def test_prevent_login_of_nonsuperusers(self):
        self.client.force_authenticate(None)
        assert_api_license_error(self.client.post(reverse('auth-login'), data={
            'username': self.user_regular.username,
            'password': self.password
        }))

    def test_prevent_login_of_system_users(self):
        assert_api_license_error(self.client.post(reverse('auth-login'), data={
            'username': self.user_system.username,
            'password': self.password,
        }))

    def test_prevent_create_non_superusers(self):
        self.user_regular.delete()
        assert_api_license_error(self.client.post(reverse('pentestuser-list'), data={
            'username': 'new-user1',
            'password': self.password,
            'is_superuser': False,
        }))

        assert self.client.post(reverse('pentestuser-list'), data={
            'username': 'new-user2',
            'password': self.password,
            'is_superuser': True,
        }).status_code == 201

    @override_settings(LOCAL_USER_AUTH_ENABLED=False)
    def test_local_auth_always_enabled(self):
        self.client.logout()
        res = self.client.post(reverse('auth-login'), data={'username': self.user.username, 'password': self.password})
        assert res.status_code == 200

    def test_prevent_login_remoteuser(self):
        self.client.logout()
        assert_api_license_error(self.client.post(reverse('auth-login-remoteuser')))

    def test_prevent_login_oidc(self):
        self.client.logout()
        assert_api_license_error(self.client.post(reverse('auth-login-oidc-begin', kwargs={'oidc_provider': 'azure'})))
        assert_api_license_error(self.client.post(reverse('auth-login-oidc-complete', kwargs={'oidc_provider': 'azure'})))

    def test_prevent_create_system_users(self):
        with pytest.raises(license.LicenseError):
            create_user(is_superuser=True, is_system_user=True)

    def test_user_count_limit(self):
        # Fill max number of superusers
        self.user_system.is_system_user = False
        self.user_system.is_superuser = True
        self.user_system.save()

        # Create user: Try to exceed limit by creating new superusers
        with pytest.raises(license.LicenseLimitExceededError):
            create_user(is_superuser=True)
        assert_api_license_error(self.client.post(reverse('pentestuser-list'), data={
            'username': 'new-user3',
            'password': self.password,
            'is_superuser': True
        }))

        # Update is_superuser: Try to exceed limit by making existing users superusers
        with pytest.raises(license.LicenseError):
            self.user_regular.is_superuser = True
            self.user_regular.save()
        assert_api_license_error(self.client.patch(reverse('pentestuser-detail', kwargs={'pk': self.user_regular.pk}), data={'is_superuser': True}))

        # Disable user: should be allowed
        self.user_regular.is_active = False
        self.user_regular.is_superuser = True
        self.user_regular.save()

        # Update is_active: Try to exceed limit by enabling disabled superusers
        with pytest.raises(license.LicenseError):
            self.user_regular.is_active = True
            self.user_regular.save()
    

@pytest.mark.django_db
class TestProfessionalLicenseRestrictions:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.password = get_random_string(length=32)
        self.user = create_user(is_user_manager=True, password=self.password)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

        with mock.patch('reportcreator_api.utils.license.check_license', lambda: {'type': license.LicenseType.PROFESSIONAL, 'users': 1, 'error': None}):
            yield

    def test_user_count_limit(self):
        with pytest.raises(license.LicenseLimitExceededError):
            create_user(username='new-user1', password=self.password)
        assert_api_license_error(self.client.post(reverse('pentestuser-list'), data={
            'username': 'new-user2',
            'password': self.password,
        }))


@pytest.mark.django_db
class TestLicenseValidation:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.license_private_key, self.license_public_key = self.generate_signing_key()
        with override_settings(LICENSE_VALIDATION_KEYS=[self.license_public_key]):
            yield

    def generate_signing_key(self):
        private_key = ECC.generate(curve='ed25519')
        public_key = {
            'id': str(uuid4()),
            'algorithm': 'ed25519',
            'key': b64encode(private_key.public_key().export_key(format='DER')).decode()
        }
        return private_key, public_key

    def sign_license_data(self, license_data_str: str, public_key: dict, private_key):
        signer = eddsa.new(key=private_key, mode='rfc8032')
        signature = signer.sign(SHA512.new(license_data_str.encode()))
        return {
            'key_id': public_key['id'],
            'algorithm': public_key['algorithm'],
            'signature': b64encode(signature).decode(),
        }
    
    def sign_license(self, license_data, keys):
        license_data_str = json.dumps(license_data)
        return b64encode(json.dumps({
            'data': license_data_str,
            'signatures': [self.sign_license_data(license_data_str, k[0], k[1]) for k in keys]
        }).encode()).decode()

    def signed_license(self, **kwargs):
        return self.sign_license({
            'users': 10,
            'valid_from': (timezone.now() - timedelta(days=30)).date().isoformat(),
            'valid_until': (timezone.now() + timedelta(days=30)).date().isoformat(),
        } | kwargs, [(self.license_public_key, self.license_private_key)])

    @pytest.mark.parametrize('license_str,error', [
        (None, None),
        ('', None),
        ('asdf', 'load'),
        (b64encode(b'asdf'), 'load'),
        (b64encode(json.dumps({'data': '{"valid_from": "2000-01-01", "valid_to": "3000-01-01", "users": 10}', 'signatures': []}).encode()), 'no valid signature'),  # Missing signatures
    ])
    def test_invalid_license_format(self, license_str, error):
        license_info = license.decode_and_validate_license(license_str)
        assert (license_info['type'] == license.LicenseType.PROFESSIONAL) is False
        if error:
            assert error in license_info['error'].lower()
        else:
            assert error is None

    @pytest.mark.parametrize('valid,license_data,error', [
        (False, {'valid_from': '3000-01-01'}, 'not yet valid'),
        (False, {'valid_until': '2000-01-1'}, 'expired'),
        (False, {'users': -10}, 'user count'),
        (False, {'users': 0}, 'user count'),
        (True, {}, None),
    ])
    def test_license_validation(self, valid, license_data, error):
        license_info = license.decode_and_validate_license(self.signed_license(**license_data))
        assert (license_info['type'] == license.LicenseType.PROFESSIONAL) is valid
        if not valid:
            assert error in license_info['error'].lower()
        else:
            assert not license_info['error']

    def test_user_limit_exceeded(self):
        create_user()
        create_user()

        license_info = license.decode_and_validate_license(self.signed_license(users=1))
        assert license_info['type'] != license.LicenseType.PROFESSIONAL
        assert 'limit exceeded' in license_info['error']

    def test_invalid_signature(self):
        license_data = json.dumps({
            'users': 10,
            'valid_from': '2000-01-01',
            'valid_until': '3000-01-01',
        })
        signer = eddsa.new(key=ECC.generate(curve='ed25519'), mode='rfc8032')
        signature = signer.sign(SHA512.new(license_data.encode()))
        license_info = license.decode_and_validate_license(b64encode(json.dumps({
            'data': license_data,
            'signatures': [{
                'key_id': self.license_public_key['id'],
                'algorithm': self.license_public_key['algorithm'],
                'signature': b64encode(signature).decode(),
            }]
        }).encode()).decode())
        assert license_info['type'] != license.LicenseType.PROFESSIONAL
        assert 'no valid signature' in license_info['error'].lower()

    def test_multiple_signatures_only_1_valid(self):
        license_1 = self.signed_license()
        license_content = json.loads(b64decode(license_1))
        license_content['signatures'].append({
            'key_id': str(uuid4()),
            'algorithm': 'ed25519',
            'signature': b64encode(eddsa.new(key=ECC.generate(curve='ed25519'), mode='rfc8032').sign(SHA512.new(license_content['data'].encode()))).decode(),
        })
        license_2 = b64encode(json.dumps(license_content).encode())
        license_info = license.decode_and_validate_license(license_2)
        assert license_info['type'] == license.LicenseType.PROFESSIONAL
