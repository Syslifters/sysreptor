from django.contrib import admin

from sysreptor.notifications.models import NotificationSpec, UserNotification
from sysreptor.utils.admin import BaseAdmin


@admin.register(NotificationSpec)
class NotificationSpecAdmin(BaseAdmin):
    list_display = ['id', 'title', 'created', 'active_until', 'visible_for_days']


@admin.register(UserNotification)
class UserNotificationAdmin(BaseAdmin):
    list_display = ['id', 'notification', 'user', 'created', 'visible_until', 'read']

