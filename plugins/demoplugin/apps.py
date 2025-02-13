import logging

from reportcreator_api.conf.plugins import PluginConfig
from reportcreator_api.utils.configuration import configuration
from reportcreator_api.utils.fielddefinition.types import FieldDefinition, StringField

log = logging.getLogger(__name__)


class DemoPluginConfig(PluginConfig):
    """
    This is a demo plugin that demonstrates the plugin system.
    Use this plugin as a reference to develop your own plugins.

    This doc string is used as the plugin description in the settings page.
    """

    plugin_id = 'db365aa0-ed36-4e90-93b6-a28effc4ed47'

    configuration_definition = FieldDefinition(fields=[
        StringField(
            id='PLUGIN_DEMOPLUGIN_SETTING', 
            default='default value',
            help_text='Here you can define available plugin settings. '
            'Settings can be configured as environment variables or via the API (stored in database). '
            'It is recommended to follow the nameing convention "PLUGIN_<PLUGIN_NAME>_<SETTING_NAME>".'),
    ])

    def ready(self) -> None:
        # Perform plugin initialization
        # e.g. register signal handlers, do some monkey patching, etc.
        log.info('Loading DemoPlugin...')

        from . import signals  # noqa

    def get_frontend_settings(self, request):
        # Pass settings to JavaScript frontend.
        # Use the value of the setting defined in configuration_definition.
        return {
            'setting_value': configuration.PLUGIN_DEMOPLUGIN_SETTING,
        }