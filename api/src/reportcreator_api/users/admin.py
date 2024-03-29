from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from reportcreator_api.users.models import AuthIdentity, MFAMethod, PentestUser
from reportcreator_api.utils.admin import BaseAdmin, admin_change_url


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

