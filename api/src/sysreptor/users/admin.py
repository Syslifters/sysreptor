import json

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from sysreptor.users.models import APIToken, AuthIdentity, MFAMethod, PentestUser, Session
from sysreptor.utils.admin import BaseAdmin, admin_change_url


@admin.register(PentestUser)
class PentestUserAdmin(BaseUserAdmin):
    list_display = ['id', 'username', 'name', 'email', 'is_active', 'is_superuser', 'created']

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ( "email", "phone", "mobile", "title_before", "first_name", "middle_name", "last_name", "title_after")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_system_user",
                    "is_project_admin",
                    "is_user_manager",
                    "is_designer",
                    "is_template_editor",
                    "is_guest",
                    "is_global_archiver",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )


@admin.register(MFAMethod)
class MFAMethodAdmin(BaseAdmin):
    list_display = ['id', 'user', 'method_type', 'name', 'created']

    def link_user(self, obj):
        return admin_change_url(obj.user.name, 'users', 'pentestuser', obj.user.id)


@admin.register(AuthIdentity)
class AuthIdentityAdmin(BaseAdmin):
    list_display = ['id', 'user', 'provider', 'identifier', 'created']

    def link_user(self, obj):
        return admin_change_url(obj.user.name, 'users', 'pentestuser', obj.user.id)


@admin.register(APIToken)
class APITokenAdmin(BaseAdmin):
    list_display = ['id', 'user', 'name', 'expire_date', 'admin_permissions_enabled', 'created']


@admin.register(Session)
class SessionAdmin(BaseAdmin):
    list_display = ['id', 'user', 'created', 'expire_date']
    list_filter = ['user']
    ordering = ['-created']
    fields = ['id', 'session_key', 'created', 'updated', 'expire_date', 'user', 'decoded_session_data']
    readonly_fields = fields

    @admin.display(description='Session data')
    def decoded_session_data(self, obj):
        return format_html(
            '<pre style="white-space: pre-wrap;">{}</pre>',
            json.dumps(obj.get_decoded(), indent=2, default=str),
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
