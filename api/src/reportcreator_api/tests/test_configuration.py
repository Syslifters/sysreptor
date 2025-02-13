import json
import os
from unittest import mock

import pytest
from django.test import override_settings
from django.urls import reverse

from reportcreator_api.api_utils.models import DbConfigurationEntry
from reportcreator_api.tests.mock import api_client, create_user, override_configuration
from reportcreator_api.utils.configuration import configuration
from reportcreator_api.utils.fielddefinition.types import (
    BooleanField,
    FieldDefinition,
    JsonField,
    ListField,
    StringField,
)
from reportcreator_api.utils.utils import copy_keys


@pytest.mark.django_db()
class TestConfiguration:
    @pytest.fixture(autouse=True)
    def setUp(self):
        user = create_user(is_superuser=True)
        user.admin_permissions_enabled = True
        self.client = api_client(user)

        with override_settings(CONFIGURATION_DEFINITION_CORE=FieldDefinition(fields=[
            BooleanField(id='FIELD_BOOLEAN', default=True),
            StringField(id='FIELD_STRING', default='default value', required=True),
            JsonField(id='FIELD_JSON', default=json.dumps({'value': 'default'}), required=False),
            ListField(id='FIELD_LIST', items=StringField(), required=True),
        ])), mock.patch('reportcreator_api.conf.plugins.available_plugins', new=[]):
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
        res = self.client.patch(reverse('configuration-list'), data={'FIELD_STRING': 'api'})
        assert res.data['FIELD_STRING'] == 'env'
        assert configuration.FIELD_STRING == 'env'
        assert not DbConfigurationEntry.objects.filter(name='FIELD_STRING').exists()

