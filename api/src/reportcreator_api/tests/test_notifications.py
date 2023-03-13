import pytest
import uuid
from unittest import mock
from asgiref.sync import async_to_sync
from datetime import timedelta
from django.test import override_settings
from django.utils import timezone
from reportcreator_api.notifications.tasks import fetch_notifications

from reportcreator_api.tests.mock import create_user
from reportcreator_api.tests.utils import assertKeysEqual
from reportcreator_api.users.models import PentestUser
from reportcreator_api.notifications.models import NotificationSpec


@pytest.mark.django_db
class TestNotifications:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user_regular = create_user(username='regular')
        self.user_template_editor = create_user(username='template_editor', is_template_editor=True)
        self.user_designer = create_user(username='designer', is_designer=True)
        self.user_user_manager = create_user(username='user_manager', is_user_manager=True)
        self.user_superuser = create_user(username='superuser', is_superuser=True)
    
    @pytest.mark.parametrize('notification,expected_users', [
        (NotificationSpec(), ['regular', 'template_editor', 'designer', 'user_manager', 'superuser']),
        (NotificationSpec(active_until=(timezone.now() - timedelta(days=10)).date()), []),
        (NotificationSpec(user_conditions={'is_superuser': True}), ['superuser']),
        (NotificationSpec(user_conditions={'is_superuser': False}), ['regular', 'template_editor', 'designer', 'user_manager']),
        (NotificationSpec(user_conditions={'is_user_manager': True}), ['user_manager']),
        (NotificationSpec(user_conditions={'is_designer': True}), ['designer']),
        (NotificationSpec(user_conditions={'is_template_editor': True}), ['template_editor']),
        (NotificationSpec(user_conditions={'is_superuser': False, 'is_user_manager': False, 'is_designer': False, 'is_template_editor': False}), ['regular']),
    ])
    def test_user_conditions(self, notification, expected_users):
        # Test queryset filter
        assert set(NotificationSpec.objects.users_for_notification(notification).values_list('username', flat=True)) == set(expected_users)

        # Assigned to correct users
        notification.save()
        assert set(notification.usernotification_set.values_list('user__username', flat=True)) == set(expected_users)

        # Reverse filter
        for u in PentestUser.objects.filter(username__in=expected_users):
            assert notification in NotificationSpec.objects.notifications_for_user(u)
    
    @pytest.mark.parametrize('expected,notification,instance_settings', [
        (True, NotificationSpec(), {}),

        (True, NotificationSpec(instance_conditions={'any_tag': ['test1']}), {'INSTANCE_TAGS': ['test1']}),
        (True, NotificationSpec(instance_conditions={'any_tag': ['test1']}), {'INSTANCE_TAGS': ['test1', 'test2']}),
        (True, NotificationSpec(instance_conditions={'any_tag': ['test1', 'other']}), {'INSTANCE_TAGS': ['test1', 'test2']}),
        (False, NotificationSpec(instance_conditions={'any_tag': ['other']}), {'INSTANCE_TAGS': ['test1', 'test2']}),

        (True, NotificationSpec(instance_conditions={'version': '1.0'}), {'VERSION': '1.0'}),
        (True, NotificationSpec(instance_conditions={'version': '==1.0'}), {'VERSION': '1.0'}),

        (True, NotificationSpec(instance_conditions={'version': '>=1.0'}), {'VERSION': '1.5'}),
        (True, NotificationSpec(instance_conditions={'version': '>=1.0'}), {'VERSION': '1.0'}),
        (True, NotificationSpec(instance_conditions={'version': '>=1.0'}), {'VERSION': '2.1'}),
        (False, NotificationSpec(instance_conditions={'version': '>=1.0'}), {'VERSION': '0.9'}),

        (True, NotificationSpec(instance_conditions={'version': '<=1.0'}), {'VERSION': '0.9.7'}),
        (True, NotificationSpec(instance_conditions={'version': '<=1.0'}), {'VERSION': '1.0'}),
        (False, NotificationSpec(instance_conditions={'version': '<=1.0'}), {'VERSION': 'dev'}),
        (False, NotificationSpec(instance_conditions={'version': '<=2'}), {'VERSION': '10.1'}),

        (True, NotificationSpec(instance_conditions={'version': '>1.0'}), {'VERSION': '1.5'}),
        (True, NotificationSpec(instance_conditions={'version': '>1.1'}), {'VERSION': '2.1'}),
        (False, NotificationSpec(instance_conditions={'version': '>1.0'}), {'VERSION': '0.9'}),
        (False, NotificationSpec(instance_conditions={'version': '>1.1'}), {'VERSION': '1.1'}),

        (True, NotificationSpec(instance_conditions={'version': '<1.0'}), {'VERSION': '0.9.7'}),
        (False, NotificationSpec(instance_conditions={'version': '<1.0'}), {'VERSION': '1.0'}),
        (False, NotificationSpec(instance_conditions={'version': '<1.0'}), {'VERSION': 'dev'}),
        (False, NotificationSpec(instance_conditions={'version': '<2'}), {'VERSION': '10.1'}),

        (True, NotificationSpec(instance_conditions={'version': 'dev'}), {'VERSION': 'dev'}),
        (False, NotificationSpec(instance_conditions={'version': 'prod'}), {'VERSION': 'dev'}),
    ])
    def test_instance_conditions(self, expected, notification, instance_settings):
        with override_settings(**instance_settings):
            # Test filter
            assert NotificationSpec.objects.check_instance_conditions(notification) == expected

            # Test assigned to users
            notification.save()
            assert notification.usernotification_set.exists() == expected

    def test_visible_for(self):
        assert NotificationSpec.objects.create(visible_for_days=10).usernotification_set.first().visible_until.date() == (timezone.now() + timedelta(days=10)).date()
        assert NotificationSpec.objects.create(visible_for_days=None).usernotification_set.first().visible_until is None


@pytest.mark.django_db
class TestNotificationImport:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user_notification = create_user(is_superuser=True)
        self.user_no_notification = create_user()

        self.notification_import_data = [
            {
                "id": uuid.UUID("fb0f0d11-41d1-4df7-9807-8d77b979adeb"),
                "created": "2023-01-26T10:27:07.517334Z",
                "updated": "2023-01-26T10:27:07.522920Z",
                "active_until": None,
                "visible_for_days": 14,
                "instance_conditions": {},
                "user_conditions": {
                    "is_superuser": True
                },
                "title": "Test",
                "text": "Test",
                "link_url": ""
            }
        ]
        async def mock_fetch_notifications_request():
            return self.notification_import_data
        with mock.patch('reportcreator_api.notifications.tasks.fetch_notifications_request', mock_fetch_notifications_request), \
             override_settings(NOTIFICATION_IMPORT_URL='https://example.com/'):
            yield
    
    def test_create(self):
        async_to_sync(fetch_notifications)(None)
        n = NotificationSpec.objects.get()
        assertKeysEqual(n, self.notification_import_data[0], ['id', 'title', 'text', 'link_url', 
            'active_until', 'visible_for_days', 'instance_conditions', 'user_conditions'])
        assert self.user_notification.notifications.get().notification == n
        assert self.user_no_notification.notifications.count() == 0
    
    def test_refetch(self):
        async_to_sync(fetch_notifications)(None)
        before = NotificationSpec.objects.get()
        async_to_sync(fetch_notifications)(None)
        after = NotificationSpec.objects.get()
        assertKeysEqual(before, after, ['id', 'created', 'updated', 'active_until'])
    
    def test_delete(self):
        async_to_sync(fetch_notifications)(None)
        self.notification_import_data = []
        async_to_sync(fetch_notifications)(None)
        after = NotificationSpec.objects.get()
        assert after.active_until < timezone.now().date()