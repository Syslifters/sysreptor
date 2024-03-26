from django.contrib import admin

from reportcreator_api.utils.admin import BaseAdmin
from reportcreator_api.notifications.models import NotificationSpec, UserNotification


@admin.register(NotificationSpec)
class NotificationSpecAdmin(BaseAdmin):
    list_display = ['id', 'title', 'created', 'active_until', 'visible_for_days']


@admin.register(UserNotification)
class UserNotificationAdmin(BaseAdmin):
    list_display = ['id', 'notification', 'user', 'created', 'visible_until', 'read']

