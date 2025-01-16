import json

from decouple import config
from reportcreator_api.conf.plugins import PluginConfig


class CustomThemePluginConfig(PluginConfig):
    plugin_id = 'd94bc997-e52e-4e5d-9b6f-6e6ffd1b7be4'

    frontend_settings = {
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
    }

    def ready(self) -> None:
        # Load settings from environment variable (with default values)
        self.frontend_settings = config('PLUGIN_CUSTOMIZETHEME_CONFIG', cast=json.loads, default=json.dumps(self.frontend_settings))

    def get_frontend_settings(self, request) -> dict:
        # Pass settings to frontend
        return self.frontend_settings
