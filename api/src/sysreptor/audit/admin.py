import json

from django.contrib import admin
from django.utils.html import format_html

from sysreptor.audit.models import AuditLogEntry
from sysreptor.users.models import PentestUser
from sysreptor.utils import license
from sysreptor.utils.admin import BaseAdmin, admin_change_url


@admin.register(AuditLogEntry)
class AuditLogEntryAdmin(BaseAdmin):
    list_display = ['created', 'type', 'actor_link', 'related_link', 'data_summary']
    list_filter = ['type', 'created', 'actor']
    search_fields = ['type']
    ordering = ['-created']
    exclude = ['data', 'related', 'content_type', 'object_id', 'actor']

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
        return [
            f.name for f in self.model._meta.fields
            if f.name not in ('data', 'content_type', 'object_id', 'related', 'actor')
        ] + ['actor_link', 'related_link', 'data_pretty']

    def data_summary(self, obj):
        return json.dumps(obj.data, default=str)[:120]

    data_summary.short_description = 'Data'

    def data_pretty(self, obj):
        return format_html('<pre style="white-space: pre-wrap;">{}</pre>', json.dumps(obj.data, indent=2, default=str))

    data_pretty.short_description = 'Data'

    def actor_link(self, obj):
        if not obj.actor_id:
            return '-'
        label = (obj.data or {}).get('actor_name') or str(obj.actor_id)
        try:
            if obj.actor is not None:
                return admin_change_url(label, 'users', 'pentestuser', obj.actor_id)
        except PentestUser.DoesNotExist:
            pass
        return f'{label} (users.pentestuser / {obj.actor_id}) (deleted)'

    actor_link.short_description = 'Actor'

    def related_link(self, obj):
        if not obj.content_type_id or not obj.object_id:
            return '-'
        label = (obj.data or {}).get('related_name') or str(obj.object_id)
        if obj.related is not None:
            return admin_change_url(label, obj.content_type.app_label, obj.content_type.model, obj.object_id)
        return f'{label} ({obj.content_type.app_label}.{obj.content_type.model} / {obj.object_id}) (deleted)'

    related_link.short_description = 'Related'
