import functools
import json
import logging
import os
import signal

import psutil
from decouple import strtobool
from django.conf import settings
from django.db import transaction

from reportcreator_api.pentests.customfields.serializers import serializer_from_definition
from reportcreator_api.pentests.customfields.types import (
    FieldDataType,
    FieldDefinition,
)
from reportcreator_api.pentests.customfields.utils import HandleUndefinedFieldsOptions, ensure_defined_structure


class Configuration:
    # For unit testing
    _force_override = {}

    @property
    def definition(self) -> FieldDefinition:
        from reportcreator_api.conf import plugins

        out = settings.CONFIGURATION_DEFINITION_CORE
        for plugin in plugins.available_plugins:
            if plugin.configuration_definition:
                out |= plugin.configuration_definition

        # Add info whether settings are set as environment variables
        for f in out.fields:
            f.extra_info |= {
                'set_in_env': f.id in os.environ,
            }
        return out

    @functools.cached_property
    def all_configurations(self) -> dict:
        from reportcreator_api.api_utils.models import DbConfigurationEntry

        definition = self.definition
        db_values = dict(DbConfigurationEntry.objects.filter(name__in=definition.keys()).values_list('name', 'value'))

        out = {}
        for f in definition.fields:
            if f.id in self._force_override:
                value = self._force_override[f.id]
            elif f.id in os.environ:
                value = self._load_env_value(definition=f, value=os.environ[f.id])
            else:
                value = self._decode_json_value(value=db_values.get(f.id))
            out[f.id] = self._validate_configuration_value(definition=f, value=value)
        return out

    def _decode_json_value(self, value):
        if value is not None:
            try:
                value = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                value = None
        return value

    def _encode_json_value(self, value):
        if value is None:
            return None
        return json.dumps(value)

    def _load_env_value(self, definition, value):
        try:
            if (load_from_env := definition.extra_info.get('load_from_env')):
                return load_from_env(os.environ[definition.id])
            elif definition.type == FieldDataType.BOOLEAN:
                return False if not value else bool(strtobool(value))
            elif definition.type in [FieldDataType.LIST, FieldDataType.OBJECT, FieldDataType.NUMBER]:
                return self._decode_json_value(value=value)
            else:
                return value
        except Exception:
            return None

    def _validate_configuration_value(self, definition, value):
        value = ensure_defined_structure(value=value, definition=definition, handle_undefined=HandleUndefinedFieldsOptions.FILL_DEFAULT)
        serializer = serializer_from_definition(definition=FieldDefinition(fields=[definition]), validate_values=True, data={definition.id: value})
        if serializer.is_valid(raise_exception=False):
            return serializer.validated_data[definition.id]
        return getattr(definition, 'default', None)

    def refresh_from_db(self):
        # Clear cached_property
        self.__dict__.pop('all_configurations', None)
        return self.all_configurations

    def get(self, name):
        if name not in self.all_configurations:
            raise KeyError(f'Unknown setting: {name}')
        return self.all_configurations[name]

    def __getattr__(self, name):
        if name in ['definition', 'all_configurations']:
            return getattr(self.__class__, name).__get__(self)
        return self.get(name)

    @transaction.atomic
    def update(self, settings: dict):
        from reportcreator_api.api_utils.models import DbConfigurationEntry

        definition = self.definition

        settings_to_update = []
        for name, value in settings.items():
            if configuration.get(name) != value and not definition[name].extra_info.get('set_in_env'):
                settings_to_update.append(DbConfigurationEntry(
                    name=name,
                    value=self._encode_json_value(value=value),
                ))

        DbConfigurationEntry.objects.filter(name__in=[s.name for s in settings_to_update]).delete()
        DbConfigurationEntry.objects.bulk_create(settings_to_update)

        # Reload cache
        return self.refresh_from_db()


configuration = Configuration()


def reload_server():
    server_proc = psutil.Process(os.getppid())
    if server_proc.name() == 'gunicorn':
        # Reload guincorn application. Restart all worker processes.
        # https://docs.gunicorn.org/en/latest/faq.html#how-do-i-reload-my-application-in-gunicorn
        # TODO: test server reload; test for downtimes
        os.kill(server_proc.pid, signal.SIGHUP)
    else:
        logging.warning('Server reload not supported')



# TODO: move settings to UI
# * [x] model
#   * [x] DbConfigurationEntry
#   * [x] cache in memory to reduce DB queries
#   * [x] env overrides db
#   * [x] rename dbsettings to configuration
# * [x] migrations
#   * [x] create DB table
#   * [x] migrate settings from env variables => no when env loading is implemented
# * [ ] settings definition
#   * [x] data types
#   * [x] validation
#   * [x] help text
#   * [x] custom env loader
#   * [x] pro only / community
# * [ ] refactor settings usage
#   * [ ] application settings
#   * [ ] enabled plugins
#   * [ ] refactor settings usage
#   * [ ] refactor plugin settings usage
# * [ ] API
#   * [x] get/set settings
#   * [x] get definition
#   * [x] pass some extra_info keys to frontend
#   * [ ] reload gunicorn on save
# * [ ] refactor plugin loading
#   * [ ] enabled_plugins from DB
#   * [ ] how to handle commands: migrate, backup, restore, collectstatic, etc.
# * [ ] frontend
#   * [x] add menu entry to admin section
#   * [x] view/edit settings
#   * [x] help-text
#   * [x] disable env settings + user infp
#   * [x] show enabled plugins (read-only)
#   * [ ] warning before saving (only first time?): server restart + reload frontend
#   * [x] DynamicInputField
#       * [x] show id on label missing
#       * [x] help-text (top-level only)
#       * [x] show errors
# * [ ] tests
#   * [ ] test_api
#   * [ ] test_settings
#   * [ ] test_plugins: setting definition, setting available, setting access, settings of availalbe_plugins shown, test enable/disable plugin
#   * [x] test priority: override > env > db > default
#   * [ ] test set_in_env: cannot change value via API
#   * [ ] override_configuration usage
# * [ ] docs
#   * [ ] rewrite setup/configuration
#   * [ ] settings loading: env > db > default
# * [ ] changelog
#   * [ ] number field: minimum, maximum
#   * [ ] application settings in UI
#   * [ ] plugin settings in UI
