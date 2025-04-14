from django.contrib import admin

from sysreptor.tasks.models import PeriodicTask
from sysreptor.utils.admin import BaseAdmin


@admin.register(PeriodicTask)
class PeriodicTaskAdmin(BaseAdmin):
    list_display = ['id', 'status', 'started', 'completed', 'last_success']

