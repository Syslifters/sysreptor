
from urllib.parse import urlencode, urlunsplit

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html


class BaseAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    ordering = ['-created']

    def get_readonly_fields(self, request, obj):
        readonly_fields = super().get_readonly_fields(request, obj)
        return readonly_fields + tuple(set([f for f in dir(self) if f.startswith('link_')]).difference(readonly_fields))


def admin_url(label, app_name, model_name, type_name, params=None, *args, **kwargs):
    admin_url_query = ''
    if params:
        admin_url_query = urlencode(params)

    admin_path = reverse('admin:%s_%s_%s' % (app_name, model_name, type_name), args=args, kwargs=kwargs)
    admin_url = urlunsplit(['', '', admin_path, admin_url_query, ''])
    return format_html('<a href="{}">{}</a>', admin_url, label)


def admin_change_url(label, app_name, model_name, object_id, params=None):
    return admin_url(label, app_name, model_name, 'change', params, object_id)


def admin_changelist_url(label, app_name, model_name, params=None):
    return admin_url(label, app_name, model_name, 'changelist', params)