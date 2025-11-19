import json
import os
from unittest import mock

import pytest
from django.core import mail
from django.core.management import CommandError, call_command
from django.test import override_settings
from django.urls import reverse
from django.utils.crypto import get_random_string

from sysreptor.api_utils.models import DbConfigurationEntry
from sysreptor.management.commands import sendtestemail
from sysreptor.tests.mock import api_client, create_user, override_configuration
from sysreptor.utils.configuration import configuration
from sysreptor.utils.fielddefinition.types import (
    BooleanField,
    FieldDefinition,
    JsonField,
    ListField,
    StringField,
)
from sysreptor.utils.utils import copy_keys


@pytest.mark.django_db()
class TestConfiguration:
    @pytest.fixture(autouse=True)
    def setUp(self):
        user = create_user(is_superuser=True, admin_permissions_enabled=True)
        self.client = api_client(user)

        with override_settings(CONFIGURATION_DEFINITION_CORE=FieldDefinition(fields=[
            BooleanField(id='FIELD_BOOLEAN', default=True),
            StringField(id='FIELD_STRING', default='default value', required=True),
            JsonField(id='FIELD_JSON', default=json.dumps({'value': 'default'}), required=False),
            ListField(id='FIELD_LIST', items=StringField(), required=True),
            StringField(id='FIELD_INTERNAL', default='default', extra_info={'internal': True}),
        ])), mock.patch('sysreptor.conf.plugins.available_plugins', new=[]):
            configuration.clear_cache()
            yield

    @override_settings(LOAD_CONFIGURATIONS_FROM_ENV=True, LOAD_CONFIGURATIONS_FROM_DB=True)
    def test_load_priority(self):
        # Unset
        assert configuration.FIELD_JSON == '{"value": "default"}'

        # Invalid DB value
        DbConfigurationEntry.objects.all().delete()
        db_field_json = DbConfigurationEntry.objects.create(name='FIELD_JSON', value='invalid')
        configuration.clear_cache()
        assert configuration.FIELD_JSON == '{"value": "default"}'
        # Valid DB value
        db_field_json.value = '"{\\"value\\": \\"db\\"}"'
        db_field_json.save()
        configuration.clear_cache()
        assert configuration.FIELD_JSON == '{"value": "db"}'

        # Invalid environment value
        with mock.patch.dict(os.environ, {'FIELD_JSON': 'invalid'}):
            configuration.clear_cache()
            assert configuration.FIELD_JSON == '{"value": "default"}'
        # Valid environment value
        with mock.patch.dict(os.environ, {'FIELD_JSON': '{"value": "env"}'}):
            configuration.clear_cache()
            assert configuration.FIELD_JSON == '{"value": "env"}'

            # Force override test
            with override_configuration(FIELD_JSON='{"value": "override"}'):
                assert configuration.FIELD_JSON == '{"value": "override"}'

    def test_override_configuration(self):
        configuration.update({'FIELD_STRING': 'original'})

        # Mock value
        with override_configuration(FIELD_STRING='mocked'):
            assert configuration.FIELD_STRING == 'mocked'
            assert configuration.get('FIELD_STRING') == 'mocked'

        # Original value restored
        assert configuration.FIELD_STRING == 'original'

    def test_default_value_on_unset(self):
        DbConfigurationEntry.objects.all().delete()
        configuration.clear_cache()

        assert configuration.FIELD_BOOLEAN is True
        assert configuration.FIELD_STRING == 'default value'
        assert configuration.FIELD_JSON == '{"value": "default"}'
        assert configuration.FIELD_LIST is None

    def test_set_value(self):
        configuration.update({'FIELD_BOOLEAN': False, 'FIELD_STRING': 'changed', 'FIELD_JSON': '{"value": "changed"}', 'FIELD_LIST': ['changed']})
        assert configuration.FIELD_BOOLEAN is False
        assert configuration.FIELD_STRING == 'changed'
        assert configuration.FIELD_JSON == '{"value": "changed"}'
        assert configuration.FIELD_LIST == ['changed']
        assert DbConfigurationEntry.objects.get(name='FIELD_BOOLEAN').value == 'false'
        assert DbConfigurationEntry.objects.get(name='FIELD_STRING').value == '"changed"'
        assert DbConfigurationEntry.objects.get(name='FIELD_JSON').value == '"{\\"value\\": \\"changed\\"}"'
        assert DbConfigurationEntry.objects.get(name='FIELD_LIST').value == '["changed"]'

    def test_api_get(self):
        assert self.client.get(reverse('configuration-list')).data == {
            'FIELD_BOOLEAN': True,
            'FIELD_STRING': 'default value',
            'FIELD_JSON': '{"value": "default"}',
            'FIELD_LIST': None,
        }

    @pytest.mark.parametrize(('expected', 'data'), [
        (True, {'FIELD_BOOLEAN': False, 'FIELD_STRING': 'changed', 'FIELD_JSON': '{"value": "changed"}', 'FIELD_LIST': ['changed']}),
        (False, {'FIELD_BOOLEAN': 'not bool'}),
        (False, {'FIELD_STRING': None}),
        (False, {'FIELD_JSON': 'not json'}),
        (False, {'FIELD_LIST': 'not list'}),
        (False, {'FIELD_LIST': [None]}),
        (False, {'FIELD_LIST': []}),
    ])
    def test_api_update(self, expected, data):
        res = self.client.patch(reverse('configuration-list'), data=data)
        if expected:
            assert res.status_code == 200, res.data
            assert copy_keys(res.data, data.keys()) == data
            assert copy_keys(self.client.get(reverse('configuration-list')).data, data.keys()) == data
        else:
            assert res.status_code == 400, res.data

    @override_settings(LOAD_CONFIGURATIONS_FROM_ENV=True, LOAD_CONFIGURATIONS_FROM_DB=True)
    @mock.patch.dict(os.environ, {'FIELD_STRING': 'env'})
    def test_cannot_update_env_settings(self):
        assert configuration.definition['FIELD_STRING'].extra_info['set_in_env'] is True

        res = self.client.get(reverse('configuration-definition'))
        definition_field_string = next(f for f in res.data['core'] if f['id'] == 'FIELD_STRING')
        assert definition_field_string['set_in_env'] is True

        res = self.client.patch(reverse('configuration-list'), data={'FIELD_STRING': 'api'})
        assert res.data['FIELD_STRING'] == 'env'
        assert configuration.FIELD_STRING == 'env'
        assert not DbConfigurationEntry.objects.filter(name='FIELD_STRING').exists()

    @override_settings(LOAD_CONFIGURATIONS_FROM_ENV=True, LOAD_CONFIGURATIONS_FROM_DB=True)
    @mock.patch.dict(os.environ, {'FIELD_STRING': 'env'})
    def test_internal_configuration(self):
        # Not loaded from env
        assert configuration.FIELD_INTERNAL == 'default'
        assert not configuration.definition['FIELD_INTERNAL'].extra_info.get('set_in_env')

        # Loaded from DB
        DbConfigurationEntry.objects.create(name='FIELD_INTERNAL', value='"db"')
        configuration.clear_cache()
        assert configuration.FIELD_INTERNAL == 'db'

        # Can update
        configuration.update({'FIELD_INTERNAL': 'updated'})
        assert configuration.FIELD_INTERNAL == 'updated'

        # Not in definition API response
        res = self.client.get(reverse('configuration-definition'))
        assert 'FIELD_INTERNAL' not in [f['id'] for f in res.data['core']]

        # Not in values API response
        res = self.client.get(reverse('configuration-list'))
        assert 'FIELD_INTERNAL' not in res.data


class TestSendTestEmailCommand:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.from_email = 'sysreptor@example.com'
        self.to_email = 'user@example.com'
        with override_settings(
            EMAIL_HOST='mail.example.com',
            EMAIL_USER='smtp-user',
            EMAIL_PASSWORD=get_random_string(32),
            EMAIL_PORT=587,
            DEFAULT_FROM_EMAIL=self.from_email,
        ):
            yield

    def test_send_success(self):
        call_command(sendtestemail.Command(), self.to_email)
        assert len(mail.outbox) == 1
        m = mail.outbox[0]
        assert m.to == [self.to_email]
        assert m.from_email == self.from_email
        assert m.subject == 'SysReptor Test Email'

    def test_send_error(self):
        with mock.patch('sysreptor.utils.mail.send_mail', side_effect=ConnectionError()):
            with pytest.raises(ConnectionError):
                call_command(sendtestemail.Command(), self.to_email)

    @override_settings(EMAIL_HOST=None)
    def test_no_host_configured(self):
        with pytest.raises(CommandError):
            call_command(sendtestemail.Command(), self.to_email)
