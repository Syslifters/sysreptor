from django.contrib import admin

from reportcreator_api.tasks.models import PeriodicTask
from reportcreator_api.utils.admin import BaseAdmin


@admin.register(PeriodicTask)
class NotificationSpecAdmin(BaseAdmin):
    list_display = ['id', 'status', 'started', 'completed', 'last_success']

