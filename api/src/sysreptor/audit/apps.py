from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sysreptor.audit'

    def ready(self):
        from . import signals  # noqa
