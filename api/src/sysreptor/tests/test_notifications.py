import contextlib
import uuid
from datetime import timedelta
from unittest import mock

import pytest
from asgiref.sync import async_to_sync
from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from sysreptor.api_utils.models import BackupLog, BackupLogType
from sysreptor.notifications.models import NotificationType, RemoteNotificationSpec, UserNotification
from sysreptor.notifications.tasks import create_notifications, fetch_notifications
from sysreptor.pentests.import_export.import_export import export_projects, import_projects
from sysreptor.pentests.models.project import CommentAnswer
from sysreptor.tests.mock import api_client, create_comment, create_project, create_user, update
from sysreptor.tests.test_import_export import archive_to_file
from sysreptor.tests.utils import assertKeysEqual
from sysreptor.users.models import PentestUser
from sysreptor.utils import license
from sysreptor.utils.utils import copy_keys


@contextlib.contextmanager
def assert_notifications_created( expected):
    since = timezone.now()
    yield
    assert_notifications_created_since(expected=expected, since=since)


def assert_notifications_created_since(expected, since):
    notifications_actual = list(UserNotification.objects.filter(created__gte=since).order_by('type', 'user__username', 'created'))
    notifications_actual_formatted = []
    for e, n in zip(expected, notifications_actual, strict=False):
        notifications_actual_formatted.append(copy_keys(n, e.keys()))
    assert notifications_actual_formatted == expected
    return notifications_actual


@pytest.mark.django_db()
class TestRemoteNotifications:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user_regular = create_user(username='regular')
        self.user_template_editor = create_user(username='template_editor', is_template_editor=True)
        self.user_designer = create_user(username='designer', is_designer=True)
        self.user_user_manager = create_user(username='user_manager', is_user_manager=True)
        self.user_project_admin = create_user(username='project_admin', is_project_admin=True)
        self.user_superuser = create_user(username='superuser', is_superuser=True)

    @pytest.mark.parametrize(('spec', 'expected_users'), [
        (RemoteNotificationSpec(), ['regular', 'template_editor', 'designer', 'user_manager', 'project_admin', 'superuser']),
        (RemoteNotificationSpec(active_until=(timezone.now() - timedelta(days=10)).date()), []),
        (RemoteNotificationSpec(user_conditions={'is_superuser': True}), ['superuser']),
        (RemoteNotificationSpec(user_conditions={'is_superuser': False}), ['regular', 'template_editor', 'designer', 'user_manager', 'project_admin']),
        (RemoteNotificationSpec(user_conditions={'is_project_admin': True}), ['project_admin']),
        (RemoteNotificationSpec(user_conditions={'is_user_manager': True}), ['user_manager']),
        (RemoteNotificationSpec(user_conditions={'is_designer': True}), ['designer']),
        (RemoteNotificationSpec(user_conditions={'is_template_editor': True}), ['template_editor']),
        (RemoteNotificationSpec(user_conditions={'is_superuser': False, 'is_project_admin': False, 'is_user_manager': False, 'is_designer': False, 'is_template_editor': False}), ['regular']),
    ])
    def test_user_conditions(self, spec, expected_users):
        # Test queryset filter
        assert set(RemoteNotificationSpec.objects.users_for_remotenotificationspecs(spec).values_list('username', flat=True)) == set(expected_users)

        # Assigned to correct users
        spec.save()
        assert set(spec.usernotification_set.values_list('user__username', flat=True)) == set(expected_users)

        # Reverse filter
        for u in PentestUser.objects.filter(username__in=expected_users):
            assert spec in RemoteNotificationSpec.objects.remotenotificationspecs_for_user(u)

    def test_visible_for(self):
        assert RemoteNotificationSpec.objects.create(visible_for_days=10).usernotification_set.first().visible_until.date() == (timezone.now() + timedelta(days=10)).date()
        assert RemoteNotificationSpec.objects.create(active_until=(timezone.now() + timedelta(days=10)).date()).usernotification_set.first().visible_until.date() == (timezone.now() + timedelta(days=10)).date()
        assert RemoteNotificationSpec.objects.create(visible_for_days=None, active_until=None).usernotification_set.first().visible_until is None


@pytest.mark.django_db()
class TestRemoteNotificationImport:
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
                "user_conditions": {
                    "is_superuser": True,
                },
                "title": "Test",
                "text": "Test",
                "link_url": "",
            },
        ]
        async def mock_fetch_notifications_request():
            return self.notification_import_data
        with mock.patch('sysreptor.notifications.tasks.fetch_notifications_request', mock_fetch_notifications_request), \
             override_settings(NOTIFICATION_IMPORT_URL='https://example.com/'):
            yield

    def test_create(self):
        async_to_sync(fetch_notifications)(None)
        n = RemoteNotificationSpec.objects.get()
        assertKeysEqual(n, self.notification_import_data[0], ['id', 'title', 'text', 'link_url',
            'active_until', 'visible_for_days', 'user_conditions'])
        notification = self.user_notification.notifications.get()
        assert notification.remotenotificationspec == n
        assert notification.type == NotificationType.REMOTE
        assert self.user_no_notification.notifications.count() == 0

    def test_refetch(self):
        async_to_sync(fetch_notifications)(None)
        rn_before = RemoteNotificationSpec.objects.get()
        un_before = self.user_notification.notifications.get()
        async_to_sync(fetch_notifications)(None)
        rn_after = RemoteNotificationSpec.objects.get()
        assertKeysEqual(rn_before, rn_after, ['id', 'created', 'updated', 'active_until'])
        un_after = self.user_notification.notifications.get()
        assertKeysEqual(un_before, un_after, ['id', 'created', 'user', 'type', 'remotenotificationspec_id', 'visible_until', 'read', 'additional_content'])

    def test_delete(self):
        async_to_sync(fetch_notifications)(None)
        self.notification_import_data = []
        async_to_sync(fetch_notifications)(None)

        # RemoteNotificationSpec is set to inactive
        after = RemoteNotificationSpec.objects.get()
        notification = self.user_notification.notifications.get(remotenotificationspec=after)
        assert after.active_until < timezone.now().date()
        assert notification.visible_until < timezone.now()

        # User notifications are set to invisible
        un1 = self.user_notification.notifications.get(remotenotificationspec=after)
        assert un1.visible_until < timezone.now()

        # No new notifications are created
        u = create_user()
        assert u.notifications.all().count() == 0


@pytest.mark.django_db()
class TestNotificationTriggers:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user_self = create_user(username='user_self', public_key=True)
        self.user_other = create_user(username='user_other', public_key=True)
        self.project = create_project(members=[self.user_self, self.user_other])
        self.finding = self.project.findings.first()
        self.section = self.project.sections.get(section_id='other')
        self.note = self.project.notes.first()
        self.client = api_client(self.user_self)

    @pytest.mark.parametrize(('text', 'expected_users', 'existing_users'), [
        ('@user', ['user'], ['user2']),
        ('text @user text', ['user'], []),
        ('text @user.', ['user'], []),
        ('text @user. text', ['user'], []),
        ('text @user: text', ['user'], []),
        ('text @user, text', ['user'], []),
        ('text @user; text', ['user'], []),
        ('text @user? text', ['user'], []),
        ('text @user! text', ['user'], []),
        ('text\n@user', ['user'], []),
        ('@user1 @user2: text', ['user1', 'user2'], []),
        ('text: @user1\n@user2', ['user1', 'user2'], []),
        ('@user1 @user2 @user3', ['user1', 'user2', 'user3'], []),
        ('text @user@example.com: text', ['user@example.com'], []),
        ('@user-name', ['user-name'], []),
        ('@user_name', ['user_name'], []),
        ('@user.name', ['user.name'], []),

        ('not user text', [], ['user']),
        ('not text@user', [], ['user']),
        ('not @usertext', [], ['user']),
        ('not @user1@user2', [], ['user1', 'user2']),
    ])
    def test_mentioned_in_comment(self, text, expected_users, existing_users):
        users = {}
        for u in expected_users + existing_users:
            users[u] = create_user(username=u)

        # Create via signal
        expected_notifications = [{'type': NotificationType.COMMENTED, 'user': users[u]} for u in expected_users]
        with assert_notifications_created(expected_notifications):
            create_comment(finding=self.finding, text=text, answers_kwargs=[])

        # Collab: first, create comment with empty text, then set text
        with assert_notifications_created(expected_notifications):
            c1 = create_comment(finding=self.finding, text='', answers_kwargs=[])
            update(c1, text=text)

        # Notify all users in comment chain when an answer is created
        with assert_notifications_created(expected_notifications):
            CommentAnswer.objects.create(comment=c1, text='Answer')

        # Mentioned in answer
        c2 = create_comment(finding=self.finding, text='Comment', answers_kwargs=[])
        with assert_notifications_created(expected_notifications):
            CommentAnswer.objects.create(comment=c2, text=text)

        # Notify all users in comment chain (also from previous answers) when an answer is created
        with assert_notifications_created(expected_notifications):
            CommentAnswer.objects.create(comment=c2, text='Answer')

    @pytest.mark.parametrize('instance_type', ['finding', 'section'])
    def test_comment_created_notify_assignee(self, instance_type):
        instance = getattr(self, instance_type)
        update(instance, assignee=self.user_other)

        # user_self creates a comment on finding that is assigned to user_other
        expected_notifications = [{'type': NotificationType.COMMENTED, 'user': self.user_other}]
        with assert_notifications_created(expected_notifications):
            c = create_comment(**{instance_type: instance}, user=self.user_self, answers_kwargs=[])
        # user_self creates a comment answer on section that is assigned to user_other
        with assert_notifications_created(expected_notifications):
            CommentAnswer.objects.create(comment=c, text='Answer', user=self.user_self)

        # Do not notify yourself
        update(instance, assignee=self.user_self)
        with assert_notifications_created([]):
            c = create_comment(**{instance_type: instance}, user=self.user_self, answers_kwargs=[])
            CommentAnswer.objects.create(comment=c, text='Answer', user=self.user_self)

    @pytest.mark.parametrize('instance_type', ['finding', 'section'])
    def test_comment_answered(self, instance_type):
        # Notify creator of comment when answered
        instance = getattr(self, instance_type)
        c = create_comment(**{instance_type: instance}, user=self.user_other, text='Comment', answers_kwargs=[])
        with assert_notifications_created([{'type': NotificationType.COMMENTED, 'user': self.user_other}]):
            CommentAnswer.objects.create(comment=c, text='Answer', user=self.user_self)

    @pytest.mark.parametrize('instance_type', ['finding', 'section', 'note'])
    def test_assigned(self, instance_type):
        instance = getattr(self, instance_type)

        def update_assignee(assignee):
            url_name = {'note': 'projectnotebookpage'}.get(instance_type, instance_type)
            res = self.client.patch(reverse(f'{url_name}-detail', kwargs={'project_pk': self.project.id, 'id': getattr(instance, f'{instance_type}_id')}), data={
                'assignee': self.user_other.id,
            })
            assert res.status_code == 200, res.data

        # Notify new assignee
        with assert_notifications_created([{'type': NotificationType.ASSIGNED, 'user': self.user_other}]):
            update_assignee(self.user_other)
        # Do not notify yourself
        with assert_notifications_created([]):
            update_assignee(self.user_self)

    def test_member_added(self):
        expected_notifications = [{'type': NotificationType.MEMBER, 'user': self.user_other}]

        # Add to existing project
        p = create_project(members=[self.user_self])
        with assert_notifications_created(expected_notifications):
            self.client.patch(reverse('pentestproject-detail', kwargs={'pk': p.id}), data={
                'members': [{'id': self.user_self.id}, {'id': self.user_other.id}],
            })

        # Add to new project
        with assert_notifications_created(expected_notifications):
            self.client.post(reverse('pentestproject-list'), data={
                'name': 'Test',
                'project_type': p.project_type.id,
                'members': [{'id': self.user_self.id}, {'id': self.user_other.id}],
            })

    def test_project_finished(self):
        with assert_notifications_created([{'type': NotificationType.FINISHED, 'user': self.user_other}]):
            res = self.client.put(reverse('pentestproject-readonly', kwargs={'pk': self.project.id}), data={'readonly': True})
            assert res.status_code == 200, res.data

    def test_project_archived(self):
        update(self.project, readonly=True)
        with assert_notifications_created([
            {'type': NotificationType.ARCHIVED, 'user': self.user_other},
            {'type': NotificationType.ARCHIVED, 'user': self.user_self},
        ]):
            res = self.client.post(reverse('pentestproject-archive', kwargs={'pk': self.project.id}), data={})
            assert res.status_code == 201, res.data

    def test_project_deleted(self):
        with assert_notifications_created([
            {'type': NotificationType.DELETED, 'user': self.user_other},
            {'type': NotificationType.DELETED, 'user': self.user_self},
        ]):
            res = self.client.delete(reverse('pentestproject-detail', kwargs={'pk': self.project.id}))
            assert res.status_code == 204, res.data

    def test_no_notifications_on_copy(self):
        with assert_notifications_created([]):
            self.project.copy()

    def test_no_notifications_on_import(self):
        with assert_notifications_created([]):
            import_projects(archive_to_file(export_projects([self.project], export_all=True)))

    def test_notification_cleanup_on_project_deleted(self):
        with assert_notifications_created(
            [{'type': NotificationType.ASSIGNED, 'user': self.user_other}] * 3 +
            [{'type': NotificationType.COMMENTED, 'user': self.user_other}] * 2,
        ):
            update(self.finding, assignee=self.user_other)
            update(self.section, assignee=self.user_other)
            update(self.note, assignee=self.user_other)
            create_comment(finding=self.finding)
            create_comment(section=self.section)
        notifications_delete = [{'type': NotificationType.DELETED, 'user': self.user_other}, {'type': NotificationType.DELETED, 'user': self.user_self}]
        with assert_notifications_created(notifications_delete):
            self.project.delete()
        assert UserNotification.objects.count() == len(notifications_delete)


@pytest.mark.django_db()
class TestBackupMissingNotification:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user_superuser = create_user(is_superuser=True)
        self.user_regular = create_user()

    @pytest.mark.parametrize(('expected', 'backuplog'), [
        (True, BackupLog(type=BackupLogType.BACKUP_FINISHED, created=timezone.now() - timedelta(days=40))),
        (True, BackupLog(type=BackupLogType.RESTORE, created=timezone.now() - timedelta(days=40))),
        (True, BackupLog(type=BackupLogType.SETUP, created=timezone.now() - timedelta(days=40))),
        (True, [BackupLog(type=BackupLogType.SETUP, created=timezone.now() - timedelta(days=40)), BackupLog(type=BackupLogType.BACKUP_STARTED, created=timezone.now() - timedelta(days=10))]),

        (False, BackupLog(type=BackupLogType.BACKUP_FINISHED, created=timezone.now() - timedelta(days=10))),
        (False, BackupLog(type=BackupLogType.RESTORE, created=timezone.now() - timedelta(days=10))),
        (False, BackupLog(type=BackupLogType.SETUP, created=timezone.now() - timedelta(days=10))),
    ])
    def test_create_notification(self, expected, backuplog):
        BackupLog.objects.all().delete()
        if isinstance(backuplog, list):
            for log in backuplog:
                log.save()
        else:
            backuplog.save()

        with assert_notifications_created([{'type': NotificationType.BACKUP_MISSING, 'user': self.user_superuser}] if expected else []):
            async_to_sync(create_notifications)(None)

        # No duplicate notifications
        with assert_notifications_created([]):
            async_to_sync(create_notifications)(None)

    def test_no_notification_after_backup(self):
        BackupLog.objects.all().delete()
        BackupLog.objects.create(type=BackupLogType.SETUP, created=timezone.now() - timedelta(days=40))

        with assert_notifications_created([{'type': NotificationType.BACKUP_MISSING, 'user': self.user_superuser}]):
            async_to_sync(create_notifications)(None)

        api_client(self.user_superuser).post(reverse('utils-backup'), data={'key': settings.BACKUP_KEY})
        with assert_notifications_created([]):
            async_to_sync(create_notifications)(None)

    def test_no_notification_for_community(self):
        BackupLog.objects.all().delete()
        BackupLog.objects.create(type=BackupLogType.SETUP, created=timezone.now() - timedelta(days=40))
        with mock.patch('sysreptor.utils.license.check_license', return_value={'type': license.LicenseType.COMMUNITY, 'users': 3, 'error': None}):
            with assert_notifications_created([]):
                async_to_sync(create_notifications)(None)
