import json

from reportcreator_api.conf.plugins import PluginConfig
from reportcreator_api.pentests.customfields.types import FieldDefinition, JsonField
from reportcreator_api.utils.configuration import configuration


class CustomThemePluginConfig(PluginConfig):
    """
    This plugin allows to customize the theme of the SysReptor frontend.
    It allows to change settings of light and dark themes globally per instance.
    """

    plugin_id = 'd94bc997-e52e-4e5d-9b6f-6e6ffd1b7be4'

    configuration_definition = FieldDefinition(fields=[
        JsonField(
            id='PLUGIN_CUSTOMIZETHEME_CONFIG', 
            schema={
                'type': 'object', 
                'properties': {
                    'all': {'type': 'object'},
                    'light': {'type': 'object'},
                    'dark': {'type': 'object'},
                }, 
                'required': []
            },
            default=json.dumps({
                # applied to all themes
                # See Vuetify theme configuration
                'all': {
                    'colors': {
                        'primary': '#ff00ff',
                        'logo': '#ff00ff',

                        'risk-critical': '#8c00fc',
                        'risk-high': '#ed0003',
                        'risk-medium': '#f0d400',
                        'risk-low': '#009dff',
                        'risk-info': '#00bc00',
                    }
                },
                # settings for specific themes
                'dark': {
                    'colors': {
                        'on-background': '#74ee15',
                        'on-surface': '#74ee15',
                        'on-drawer': '#74ee15',
                        'on-header': '#74ee15',
                    },
                },
                'light': {
                    'colors': {
                        'drawer': '#39ff14',
                        'header': '#39ff14',
                        'background': '#f3f9dc',
                        'surface': '#f3f9dc',
                    }
                },
            }),
            help_text='JSON object with theme configs to override the default theme configs.'
                      'All theme configurations provided by Vuetify are supported. '
                      'See the Vuetify documentation (https://vuetifyjs.com/en/features/theme/) for more information.'
                      'Options in `all` apply to both light and dark mode. Options in `light` and `dark` apply to the respective mode only.'
        )
    ])

    def get_frontend_settings(self, request) -> dict:
        return json.loads(configuration.PLUGIN_CUSTOMIZETHEME_CONFIG)
