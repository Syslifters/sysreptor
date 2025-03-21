from django.contrib import admin
from sysreptor.utils.admin import BaseAdmin

from .models import DemoPluginModel


@admin.register(DemoPluginModel)
class TestPluginModelAdmin(BaseAdmin):
    """
    Admin interface for DemoPluginModel.
    Accessible at /admin/plugin_<plugin_id>/demopluginmodel/
    """

    list_display = ['id', 'name']
