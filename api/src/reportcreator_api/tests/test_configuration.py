import json
from unittest import mock

import pytest
from django.test import override_settings
from django.urls import reverse

from reportcreator_api.api_utils.models import DbConfigurationEntry
from reportcreator_api.pentests.customfields.types import (
    BooleanField,
    FieldDefinition,
    JsonField,
    ListField,
    StringField,
)
from reportcreator_api.tests.mock import api_client, create_user, override_configuration
from reportcreator_api.utils.configuration import configuration


@pytest.mark.django_db()
class TestConfiguration:
    @pytest.fixture(autouse=True)
    def setUp(self):
        user = create_user(is_superuser=True)
        user.admin_permissions_enabled = True
        self.client = api_client(user)

        with override_settings(CONFIGURATION_DEFINITION_CORE=FieldDefinition(fields=[
            BooleanField(id='FIELD_BOOLEAN', default=True),
            StringField(id='FIELD_STRING', default='default value'),
            JsonField(id='FIELD_JSON', default=json.dumps({'value': 'default'})),
            ListField(id='FIELD_LIST', items=StringField()),
        ])), mock.patch('reportcreator_api.conf.plugins.available_plugins', new=[]):
            configuration.refresh_from_db()
            yield

    def test_load_priority(self):
        # Unset
        assert configuration.FIELD_JSON == '{"value": "default"}'

        # Invalid DB value
        DbConfigurationEntry.objects.all().delete()
        db_field_json = DbConfigurationEntry.objects.create(name='FIELD_JSON', value='invalid')
        configuration.refresh_from_db()
        assert configuration.FIELD_JSON == '{"value": "default"}'
        # Valid DB value
        db_field_json.value = '"{\\"value\\": \\"db\\"}"'
        db_field_json.save()
        configuration.refresh_from_db()
        assert configuration.FIELD_JSON == '{"value": "db"}'

        # Invalid environment value
        with mock.patch.dict('os.environ', {'FIELD_JSON': 'invalid'}):
            configuration.refresh_from_db()
            assert configuration.FIELD_JSON == '{"value": "default"}'
        # Valid environment value
        with mock.patch.dict('os.environ', {'FIELD_JSON': '{"value": "env"}'}):
            configuration.refresh_from_db()
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
        configuration.refresh_from_db()

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

    def test_api_update(self):
        data = {
            'FIELD_BOOLEAN': False,
            'FIELD_STRING': 'changed',
            'FIELD_JSON': '{"value": "changed"}',
            'FIELD_LIST': ['changed'],
        }
        res = self.client.post(reverse('configuration-list'), data=data)
        assert res.status_code == 200, res.data
        assert res.data == data

        assert self.client.get(reverse('configuration-list')).data == data

    def test_plugin_settings_available(self):
        # TODO: mock available_plugins
        pass

