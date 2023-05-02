from django.contrib import admin

from reportcreator_api.utils.admin import BaseAdmin
from reportcreator_api.notifications.models import NotificationSpec, UserNotification


@admin.register(NotificationSpec)
class NotificationSpecAdmin(BaseAdmin):
    pass


@admin.register(UserNotification)
class UserNotificationAdmin(BaseAdmin):
    pass

