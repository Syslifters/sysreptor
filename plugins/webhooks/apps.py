import json

from reportcreator_api.conf.plugins import PluginConfig
from reportcreator_api.utils.fielddefinition.types import (
    ComboboxField,
    FieldDefinition,
    ListField,
    ObjectField,
    StringField,
)
from reportcreator_api.utils.utils import omit_items

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
                ListField(id='events', items=ComboboxField(
                    suggestions=omit_items(list(WebhookEventType), [WebhookEventType.FINDING_UPDATED, WebhookEventType.SECTION_UPDATED]) + [
                        WebhookEventType.FINDING_UPDATED + ':status',
                        WebhookEventType.FINDING_UPDATED + ':data.custom_field_id',
                        WebhookEventType.SECTION_UPDATED + ':status',
                        WebhookEventType.SECTION_UPDATED + ':data.custom_field_id',
                    ],
                    required=False), 
                    required=False),
            ]),
            required=False,
            extra_info={'load_from_env': webhooks_load_from_env}),
    ])

    def ready(self) -> None:
        from . import signals  # noqa

