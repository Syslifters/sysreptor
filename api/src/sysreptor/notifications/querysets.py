
from django.conf import settings
from django.db import models
from django.db.models import signals
from django.db.models.functions import Coalesce
from django.utils import timezone
from packaging import version

from sysreptor.utils.history import HistoricalRecords


class RemoteNotificationSpecQuerySet(models.QuerySet):
    def only_active(self):
        return self.filter(models.Q(active_until__isnull=True) | models.Q(active_until__gte=timezone.now()))


class RemoteNotificationSpecManager(models.Manager.from_queryset(RemoteNotificationSpecQuerySet)):
    def parse_version(self, version_str):
        try:
            return version.Version(version_str)
        except (version.InvalidVersion, TypeError):
            return None

    def check_version(self, version_condition):
        current_version = self.parse_version(settings.VERSION)
        if not current_version:
            if settings.VERSION and version_condition and (version_condition == settings.VERSION or version_condition == f'=={settings.VERSION}'):
                return True
            return False

        if version_condition.startswith('=='):
            return current_version == self.parse_version(version_condition[2:])
        elif version_condition.startswith('>='):
            required_version = self.parse_version(version_condition[2:])
            return required_version and current_version >= required_version
        elif version_condition.startswith('<='):
            required_version = self.parse_version(version_condition[2:])
            return required_version and current_version <= required_version
        elif version_condition.startswith('>'):
            required_version = self.parse_version(version_condition[1:])
            return required_version and current_version > required_version
        elif version_condition.startswith('<'):
            required_version = self.parse_version(version_condition[1:])
            return required_version and current_version < required_version
        else:
            return current_version == self.parse_version(version_condition)

    def users_for_remotenotificationspecs(self, notification):
        from sysreptor.users.models import PentestUser

        if notification.active_until and notification.active_until < timezone.now().date():
            return PentestUser.objects.none()

        # User conditions
        users = PentestUser.objects.all()
        for role in ['is_superuser', 'is_project_admin', 'is_designer', 'is_template_editor', 'is_user_manager']:
            if role in notification.user_conditions and isinstance(notification.user_conditions[role], bool):
                users = users.filter(**{role: notification.user_conditions[role]})

        return users

    def remotenotificationspecs_for_user(self, user):
        from sysreptor.notifications.models import RemoteNotificationSpec

        return RemoteNotificationSpec.objects \
            .only_active() \
            .filter(models.Q(user_conditions__is_superuser__isnull=True) | models.Q(user_conditions__is_superuser=user.is_superuser)) \
            .filter(models.Q(user_conditions__is_desinger__isnull=True) | models.Q(user_conditions__is_designer=user.is_designer)) \
            .filter(models.Q(user_conditions__is_template_editor__isnull=True) | models.Q(user_conditions__is_template_editor=user.is_template_editor)) \
            .filter(models.Q(user_conditions__is_user_manager__isnull=True) | models.Q(user_conditions__is_user_manager=user.is_user_manager)) \
            .filter(models.Q(user_conditions__is_project_admin__isnull=True) | models.Q(user_conditions__is_project_admin=user.is_project_admin))

    def assign_to_users(self, instance):
        from sysreptor.notifications.models import Notification, NotificationType
        users = self.users_for_remotenotificationspecs(instance) \
            .exclude(notifications__remotenotificationspec=instance)

        return Notification.objects.create_for_users(
            users=users,
            type=NotificationType.REMOTE,
            remotenotificationspec=instance,
            visible_until=instance.visible_until,
        )

    def assign_to_notifications(self, user):
        from sysreptor.notifications.models import Notification, NotificationType
        remotenotificationspecs = self.remotenotificationspecs_for_user(user)

        notifications = []
        for n in remotenotificationspecs:
            notifications.append(Notification(
                type=NotificationType.REMOTE,
                user=user,
                remotenotificationspec=n,
                visible_until=n.visible_until,
            ))
        return Notification.objects.bulk_create(notifications)

    def bulk_create(self, *args, **kwargs):
        objs = super().bulk_create(*args, **kwargs)
        for o in objs:
            signals.post_save.send(sender=o.__class__, instance=o, created=True, raw=False, update_fields=None)
        return objs


class NotificationQuerySet(models.QuerySet):
    def only_permitted(self, user):
        return self.filter(user=user)

    def only_visible(self):
        return self \
            .filter(models.Q(visible_until__isnull=True) | models.Q(visible_until__gt=timezone.now()))

    def annotate_group_order(self):
        return self.annotate(group_order=Coalesce(models.Max('project__notification__created'), models.F('created')))


class NotificationManager(models.Manager.from_queryset(NotificationQuerySet)):
    def get_created_by(self):
        return getattr(HistoricalRecords.context, 'history_user', None) or \
               getattr(getattr(HistoricalRecords.context, 'request', None), 'user', None)

    def get_prevent_notifications(self):
        return getattr(HistoricalRecords.context, 'prevent_notifications', False)

    def get_create_kwargs(self, additional_content=None, **kwargs):
        additional_content = additional_content or {}

        project = kwargs.get('project')
        finding = kwargs.get('finding')
        section = kwargs.get('section')
        note = kwargs.get('note')

        if comment := kwargs.get('comment'):
            finding = comment.finding
            section = comment.section
        if finding:
            project = finding.project
            additional_content |= {'finding_title': finding.title}
        if section:
            project = section.project
            additional_content |= {'section_title': section.title}
        if note:
            project = note.project
            additional_content |= {'note_title': note.title}
        if project:
            additional_content |= {'project_name': project.name}

        return kwargs | {
            'created_by': kwargs.get('created_by', self.get_created_by()),
            'additional_content': additional_content,
        }

    def create(self, **kwargs):
        return super().create(**self.get_create_kwargs(**kwargs))

    def create_for_users(self, users, skip_for_created_by=False, **kwargs):
        from sysreptor.pentests.models import ProjectMemberInfo

        if self.get_prevent_notifications():
            return []

        notifications = []
        for user in users:
            if isinstance(user, ProjectMemberInfo):
                user = user.user
            if not user:
                continue
            created_by = kwargs.pop('created_by', self.get_created_by())
            if skip_for_created_by and user == created_by:
                continue
            notifications.append(self.model(**self.get_create_kwargs(user=user, created_by=created_by, **kwargs)))
        return self.bulk_create(notifications)
