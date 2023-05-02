import os
from celery import Celery, signals


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reportcreator_api.conf.settings')


celery_app = Celery(
    'reportcreator',
    fixups=Celery.builtin_fixups | {
        'reportcreator_api.tasks.rendering.celery_worker:SecureWorkerFixup'
    }
)

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
celery_app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
celery_app.autodiscover_tasks()


@signals.setup_logging.connect()
def setup_logging(*args, **kwargs):
    import logging.config
    from django.conf import settings
    logging.config.dictConfig(settings.LOGGING)
