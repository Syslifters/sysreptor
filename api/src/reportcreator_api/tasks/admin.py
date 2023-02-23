from django.contrib import admin

from reportcreator_api.utils.admin import BaseAdmin
from reportcreator_api.tasks.models import PeriodicTask


@admin.register(PeriodicTask)
class NotificationSpecAdmin(BaseAdmin):
    pass

