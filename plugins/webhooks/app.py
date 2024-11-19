import json

from decouple import config
from reportcreator_api.conf.plugins import PluginConfig

from .serializers import WebhookConfigSerializer


class WebhooksPluginConfig(PluginConfig):
    plugin_id = 'b97e16cf-74a9-45bf-b0ae-8bd81929c805'
    settings = {
        'WEBHOOKS': []
    }

    def ready(self) -> None:
        self.settings = self.load_settings()

        from . import signals  # noqa

    def load_settings(self):
        webhook_configs = config('WEBHOOKS', cast=json.loads, default='[]')
        serializer = WebhookConfigSerializer(data=webhook_configs, many=True)
        serializer.is_valid(raise_exception=True)
        return {
            'WEBHOOKS': serializer.data
        }
        
