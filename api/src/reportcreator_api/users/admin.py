from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from reportcreator_api.utils.admin import BaseAdmin, admin_change_url
from reportcreator_api.users.models import PentestUser, MFAMethod


@admin.register(PentestUser)
class PentestUserAdmin(BaseUserAdmin):
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
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )


@admin.register(MFAMethod)
class MFAMethodAdmin(BaseAdmin):
    def link_user(self, obj):
        return admin_change_url(obj.user.name, 'users', 'pentestuser', obj.user.id)


