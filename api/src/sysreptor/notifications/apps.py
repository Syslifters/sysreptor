from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sysreptor.notifications'

    def ready(self) -> None:
        from . import signals  # noqa
        from . import tasks  # noqa
