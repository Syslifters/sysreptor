from django.apps import AppConfig


class AgentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sysreptor.ai'

    def ready(self):
        from . import tasks  # noqa

