import contextlib
from unittest import mock

import pytest
from asgiref.sync import async_to_sync
from django.apps import apps
from reportcreator_api.pentests.models import ArchivedProject
from reportcreator_api.tests.mock import create_finding, create_project, create_user
from reportcreator_api.utils import utils

from ..apps import WebhooksPluginConfig
from ..models import WebhookEventType


@contextlib.contextmanager
def override_webhook_settings(**kwargs):
    app = apps.get_app_config(WebhooksPluginConfig.label)
    old_settings = app.settings
    try:
        app.settings |= kwargs
        yield
    finally:
        app.settings = old_settings


def update(obj, **kwargs):
    for k, v in kwargs.items():
        setattr(obj, k, v)
    obj.save()
    return obj


@pytest.mark.django_db()
class TestWebhooksCalled:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user(public_key=True)
        self.project = create_project(members=[self.user])
        with mock.patch('sysreptor_plugins.webhooks.utils.send_webhook_request') as self.mock:
            yield

    @async_to_sync()
    async def wait_for_background_tasks(self):
        for t in utils._background_tasks:
            await t
    
    @pytest.mark.parametrize(['event', 'trigger'], [
        (WebhookEventType.PROJECT_CREATED, lambda s: create_project()),
        (WebhookEventType.PROJECT_FINISHED, lambda s: update(s.project, readonly=True)),
        (WebhookEventType.PROJECT_ARCHIVED, lambda s: ArchivedProject.objects.create_from_project(s.project)),
        (WebhookEventType.PROJECT_DELETED, lambda s: s.project.delete()),
        (WebhookEventType.FINDING_CREATED, lambda s: create_finding(s.project)),
        (WebhookEventType.FINDING_DELETED, lambda s: s.project.findings.first().delete()),
    ])
    def test_webhooks_called(self, event, trigger):
        webhook_config = {'url': 'https://example.com/webhook1', 'events': [event]}
        with override_webhook_settings(WEBHOOKS=[webhook_config, {'url': 'https://example.com/other', 'events': ['other']}]):
            self.mock.assert_not_called()
            trigger(self)
            self.wait_for_background_tasks()
            self.mock.assert_called_once()
            call_args = self.mock.call_args[1]
            assert call_args['webhook'] == webhook_config
            assert call_args['data']['event'] == event
    
    @override_webhook_settings(WEBHOOKS=[{'url': 'https://example.com/webhook1', 'events': [WebhookEventType.PROJECT_CREATED]}])
    def test_event_filter(self):
        # Not subscribed to event
        self.mock.assert_not_called()
        update(self.project, readonly=True)
        self.wait_for_background_tasks()
        self.mock.assert_not_called()

        # Subscribed to event: webhook called
        create_project()
        self.wait_for_background_tasks()
        self.mock.assert_called_once()

    @override_webhook_settings(WEBHOOKS=[
        {'url': 'https://example.com/webhook1', 'events': [WebhookEventType.PROJECT_CREATED]}, 
        {'url': 'https://example.com/webhook2', 'events': [WebhookEventType.PROJECT_CREATED]}
    ])
    def test_error_handling(self):
        self.mock.side_effect = [Exception('Request failed'), mock.DEFAULT]
        create_project()
        self.wait_for_background_tasks()
        assert self.mock.call_count == 2
