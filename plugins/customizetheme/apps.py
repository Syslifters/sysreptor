import json

from sysreptor.plugins import FieldDefinition, JsonField, PluginConfig, configuration


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
                'required': [],
            },
            default=json.dumps({
                # applied to all themes
                # See Vuetify theme configuration
                'all': {
                    'colors': {
                        'primary': '#2563eb',
                        'logo': '#475569',

                        'risk-critical': '#990000',
                        'risk-high': '#ed0003',
                        'risk-medium': '#f0d400',
                        'risk-low': '#009dff',
                        'risk-info': '#00bc00',
                    },
                    'variables': {
                        'header-logo-url': (
                            'data:image/svg+xml;base64,'
                            'PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+'
                            'PHBhdGggZD0iTTE5LDE5TDEyLDExVjE5SDVMMTIsMTFWNUgxOU0xOSwzSDVBMiwyIDAgMCwwIDMsNVYxOUEyLDIgMCAwLDAg'
                            'NSwyMUgxOUEyLDIgMCAwLDAgMjEsMTlWNUEyLDIgMCAwLDAgMTksM1oiIC8+PC9zdmc+'
                        ),
                        'header-logo-height': '32px',
                    },
                },
                # settings for specific themes
                'dark': {
                    'colors': {
                        'on-background': '#e2e8f0',
                        'on-surface': '#e2e8f0',
                        'on-drawer': '#e2e8f0',
                        'on-header': '#e2e8f0',
                    },
                },
                'light': {
                    'colors': {
                        'drawer': '#f8fafc',
                        'header': '#f8fafc',
                        'background': '#f8fafc',
                        'surface': '#f8fafc',
                    },
                },
            }),
            help_text='JSON object with theme configs to override the default theme configs.'
                      'All theme configurations provided by Vuetify are supported. '
                      'See the Vuetify documentation (https://vuetifyjs.com/en/features/theme/) for more information.'
                      'Options in `all` apply to both light and dark mode. Options in `light` and `dark` apply to the respective mode only.',
        ),
    ])

    def get_frontend_settings(self, request) -> dict:
        return json.loads(configuration.PLUGIN_CUSTOMIZETHEME_CONFIG)
