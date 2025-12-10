from django.contrib import admin

from sysreptor.notifications.models import CustomNotificationSpec, RemoteNotificationSpec, UserNotification
from sysreptor.utils.admin import BaseAdmin


@admin.register(RemoteNotificationSpec)
class RemoteNotificationSpecAdmin(BaseAdmin):
    list_display = ['id', 'title', 'created', 'active_until', 'visible_for_days']


@admin.register(CustomNotificationSpec)
class CustomNotificationSpecAdmin(BaseAdmin):
    list_display = ['id', 'title', 'created', 'active_until', 'visible_for_days']


@admin.register(UserNotification)
class UserNotificationAdmin(BaseAdmin):
    list_display = ['id', 'type', 'user', 'created', 'read']
    readonly_fields = ['project', 'finding', 'section', 'note', 'comment', 'remotenotificationspec', 'customnotificationspec']

