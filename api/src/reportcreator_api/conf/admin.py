from django.contrib.admin.apps import AdminConfig as AdminConfigBase
from django.contrib.admin.sites import AdminSite as AdminSiteBase


class AdminConfig(AdminConfigBase):
    default_site = 'reportcreator_api.conf.admin.AdminSite'


class AdminSite(AdminSiteBase):
    def has_permission(self, request):
        return request.user and not request.user.is_anonymous and request.user.is_admin

