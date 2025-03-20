from django.contrib import admin
from sysreptor.utils.admin import BaseAdmin

from .models import ProjectNumber


@admin.register(ProjectNumber)
class ProjectNumberModelAdmin(BaseAdmin):
    """
    Admin interface for ProjectNumber.
    Accessible at /admin/plugin_<plugin_id>/projectnumber/
    """
    list_display = ['current_id']
