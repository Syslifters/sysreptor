import json

from django.contrib import admin
from django.utils.html import format_html

from sysreptor.audit.models import AuditLogEntry
from sysreptor.utils import license
from sysreptor.utils.admin import BaseAdmin, admin_change_url


@admin.register(AuditLogEntry)
class AuditLogEntryAdmin(BaseAdmin):
    list_display = ['created', 'type', 'user_username', 'related_object_link', 'data_summary']
    list_filter = ['type', 'created']
    search_fields = ['user_username', 'type']
    ordering = ['-created']
    exclude = ['data']

    def has_module_permission(self, request):
        return license.is_professional() and super().has_module_permission(request)

    def has_view_permission(self, request, obj=None):
        return license.is_professional() and super().has_view_permission(request, obj)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields if f.name != 'data'] + ['data_pretty', 'related_object_link']

    def data_summary(self, obj):
        return json.dumps(obj.data, default=str)[:120]

    data_summary.short_description = 'Data'

    def data_pretty(self, obj):
        return format_html('<pre style="white-space: pre-wrap;">{}</pre>', json.dumps(obj.data, indent=2, default=str))

    data_pretty.short_description = 'Data'

    def related_object_link(self, obj):
        if not obj.content_type_id or not obj.object_id:
            return '-'
        label = (obj.data or {}).get('object_repr') or str(obj.object_id)
        if obj.related is not None:
            return admin_change_url(label, obj.content_type.app_label, obj.content_type.model, obj.object_id)
        return f'{obj.content_type.app_label}.{obj.content_type.model} / {obj.object_id} (deleted)'

    related_object_link.short_description = 'Related object'
