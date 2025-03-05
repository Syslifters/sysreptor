from unittest import mock

import pytest
from asgiref.sync import async_to_sync
from reportcreator_api.pentests.models import ArchivedProject, ReviewStatus
from reportcreator_api.tests.mock import (
    create_finding,
    create_project,
    create_user,
    override_configuration,
    update,
)
from reportcreator_api.utils import utils

from ..models import WebhookEventType


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

    @pytest.mark.parametrize(('event', 'trigger'), [
        (WebhookEventType.PROJECT_CREATED, lambda s: create_project()),
        (WebhookEventType.PROJECT_FINISHED, lambda s: update(s.project, readonly=True)),
        (WebhookEventType.PROJECT_ARCHIVED, lambda s: ArchivedProject.objects.create_from_project(s.project)),
        (WebhookEventType.PROJECT_DELETED, lambda s: s.project.delete()),
        (WebhookEventType.FINDING_CREATED, lambda s: create_finding(s.project)),
        (WebhookEventType.FINDING_DELETED, lambda s: s.project.findings.first().delete()),
        (WebhookEventType.FINDING_UPDATED, lambda s: update(s.project.findings.first(), status=ReviewStatus.READY_FOR_REVIEW)),
        (WebhookEventType.FINDING_UPDATED + ':status', lambda s: update(s.project.findings.first(), status=ReviewStatus.READY_FOR_REVIEW)),
        (WebhookEventType.FINDING_UPDATED + ':data.field_enum', lambda s: update(s.project.findings.first(), data={'field_enum': 'enum1'})),
        (WebhookEventType.SECTION_UPDATED, lambda s: update(s.project.sections.get(section_id='other'), status=ReviewStatus.READY_FOR_REVIEW)),
        (WebhookEventType.SECTION_UPDATED + ':status', lambda s: update(s.project.sections.get(section_id='other'), status=ReviewStatus.READY_FOR_REVIEW)),
        (WebhookEventType.SECTION_UPDATED + ':data.field_enum', lambda s: update(s.project.sections.get(section_id='other'), data={'field_enum': 'enum1'})),
    ])
    def test_webhooks_called(self, event, trigger):
        webhook_config = {'url': 'https://example.com/webhook1', 'events': [event]}
        with override_configuration(WEBHOOKS=[webhook_config, {'url': 'https://example.com/other', 'events': ['other']}]):
            self.mock.assert_not_called()
            trigger(self)
            self.wait_for_background_tasks()
            self.mock.assert_called_once()
            call_args = self.mock.call_args[1]
            assert call_args['webhook'] == webhook_config | {'headers': []}
            assert call_args['data']['event'] == event.split(':')[0]

    @override_configuration(WEBHOOKS=[{'url': 'https://example.com/webhook1', 'events': [WebhookEventType.PROJECT_CREATED]}])
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

    @pytest.mark.parametrize(('expected', 'field_filter', 'data'), [
        (True, 'data.field_enum', {'field_enum': 'enum1'}),
        (True, 'data.field_object.field_enum', {'field_object': {'field_enum': 'enum1'}}),
        (True, 'data.field_list', {'field_list': ['value1']}),
        (True, 'data.field_object', {'field_object': {'nested1': 'changed'}}),
        (True, 'data', {'field_enum': 'enum1'}),
        (False, 'data.field_enum', {'field_string': 'changed'}),
        (False, 'status', {'field_enum': 'enum1'}),
    ])
    def test_updated_field_filter(self, expected, field_filter, data):
        with override_configuration(WEBHOOKS=[{'url': 'https://example.com/webhook1', 'events': [WebhookEventType.FINDING_UPDATED + ':' + field_filter]}]):
            self.mock.assert_not_called()
            update(self.project.findings.first(), data=data)
            if expected:
                self.mock.assert_called_once()
                assert self.mock.call_args[1]['data']['event'] == WebhookEventType.FINDING_UPDATED
            else:
                self.mock.assert_not_called()
            
    @override_configuration(WEBHOOKS=[
        {'url': 'https://example.com/webhook1', 'events': [WebhookEventType.PROJECT_CREATED]},
        {'url': 'https://example.com/webhook2', 'events': [WebhookEventType.PROJECT_CREATED]},
    ])
    def test_error_handling(self):
        self.mock.side_effect = [Exception('Request failed'), mock.DEFAULT]
        create_project()
        self.wait_for_background_tasks()
        assert self.mock.call_count == 2
