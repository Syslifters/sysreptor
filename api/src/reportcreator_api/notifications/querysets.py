from packaging import version
from datetime import timedelta
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.db.models import signals

from reportcreator_api.utils import license


class UserNotificationQuerySet(models.QuerySet):
    def only_permitted(self, user):
        return self.filter(user=user)

    def only_visible(self):
        return self \
            .filter(models.Q(notification__active_until__isnull=True) | models.Q(notification__active_until__gt=timezone.now())) \
            .filter(models.Q(visible_until__isnull=True) | models.Q(visible_until__gt=timezone.now()))


class NotificationSpecQuerySet(models.QuerySet):
    def only_active(self):
        return self.filter(models.Q(active_until__isnull=True) | models.Q(active_until__gte=timezone.now()))


class NotificationSpecManager(models.Manager.from_queryset(NotificationSpecQuerySet)):
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

    def check_instance_conditions(self, notification):
        current_instance_tags = list(settings.INSTANCE_TAGS)
        if license.is_professional():
            current_instance_tags.append('license:professional')
        elif not license.is_professional() and not license.check_license()['error']:
            current_instance_tags.append('license:community')
        if (instance_tags := set(notification.instance_conditions.get('any_tag', []))) and not instance_tags.intersection(current_instance_tags):
            return False
        if (version_condition := notification.instance_conditions.get('version')) and not self.check_version(version_condition):
            return False
        return True
    
    def users_for_notification(self, notification):
        from reportcreator_api.users.models import PentestUser

        if notification.active_until and notification.active_until < timezone.now().date():
            return PentestUser.objects.none()
        
        # Instance conditions
        if not self.check_instance_conditions(notification):
            return PentestUser.objects.none()
        
        # User conditions
        users = PentestUser.objects.all()
        for role in ['is_superuser', 'is_designer', 'is_template_editor', 'is_user_manager']:
            if role in notification.user_conditions and isinstance(notification.user_conditions[role], bool):
                users = users.filter(**{role: notification.user_conditions[role]})
        
        return users

    def notifications_for_user(self, user):
        from reportcreator_api.notifications.models import NotificationSpec

        notifications = NotificationSpec.objects \
            .only_active() \
            .filter(models.Q(user_conditions__is_superuser__isnull=True) | models.Q(user_conditions__is_superuser=user.is_superuser)) \
            .filter(models.Q(user_conditions__is_desinger__isnull=True) | models.Q(user_conditions__is_designer=user.is_designer)) \
            .filter(models.Q(user_conditions__is_template_editor__isnull=True) | models.Q(user_conditions__is_template_editor=user.is_template_editor)) \
            .filter(models.Q(user_conditions__is_user_manager__isnull=True) | models.Q(user_conditions__is_user_manager=user.is_user_manager))
        notifications = list(filter(self.check_instance_conditions, notifications))
        return notifications

    def assign_to_users(self, notification):
        from reportcreator_api.notifications.models import UserNotification
        users = self.users_for_notification(notification) \
            .exclude(notifications__notification=notification)

        user_notifications = []
        for u in users:
            visible_until = None
            if notification.visible_for_days:
                visible_until = timezone.now() + timedelta(days=notification.visible_for_days)
            user_notifications.append(UserNotification(user=u, notification=notification, visible_until=visible_until))
        UserNotification.objects.bulk_create(user_notifications)

    def assign_to_notifications(self, user):
        from reportcreator_api.notifications.models import UserNotification
        notifications = self.notifications_for_user(user)

        user_notifications = []
        for n in notifications:
            visible_until = None
            if n.visible_for_days:
                visible_until = timezone.now() + timedelta(days=n.visible_for_days)
            user_notifications.append(UserNotification(user=user, notification=n, visible_until=visible_until))
        UserNotification.objects.bulk_create(user_notifications)

    def bulk_create(self, *args, **kwargs):
        objs = super().bulk_create(*args, **kwargs)
        for o in objs:
            signals.post_save.send(sender=o.__class__, instance=o, created=True, raw=False, update_fields=None)
        return objs
