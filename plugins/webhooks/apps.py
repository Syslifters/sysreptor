import json

from reportcreator_api.conf.plugins import PluginConfig
from reportcreator_api.utils.fielddefinition.types import (
    EnumChoice,
    EnumField,
    FieldDefinition,
    ListField,
    ObjectField,
    StringField,
)

from .models import WebhookEventType


def webhooks_load_from_env(value):
    # Reformat old data format to new format while loading
    value = json.loads(value)
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict) and isinstance(item.get('headers'), dict):
                item['headers'] = [{'name': k, 'value': v} for k, v in item['headers'].items()]
    return value


class WebhooksPluginConfig(PluginConfig):
    """
    This plugin adds webhooks to SysReptor.
    HTTP requests are sent to the configured webhooks URL when certain events occur.
    """

    plugin_id = 'b97e16cf-74a9-45bf-b0ae-8bd81929c805'
    professional_only = True
    configuration_definition = FieldDefinition(fields=[
        ListField(
            id='WEBHOOKS',
            items=ObjectField(properties=[
                StringField(id='url', pattern='^https?://.*$'),
                ListField(id='headers', items=ObjectField(properties=[
                    StringField(id='name'),
                    StringField(id='value'),
                ]), required=False),
                ListField(id='events', items=EnumField(choices=[EnumChoice(value=t) for t in list(WebhookEventType)], required=False), required=False),
            ]),
            required=False,
            extra_info={'load_from_env': webhooks_load_from_env}),
    ])

    def ready(self) -> None:
        from . import signals  # noqa

