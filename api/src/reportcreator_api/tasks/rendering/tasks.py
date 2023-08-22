from base64 import b64encode
from celery import shared_task
from django.conf import settings

from reportcreator_api.utils.logging import log_timing
from reportcreator_api.tasks.rendering import render


@shared_task(name='reportcreator.render_pdf', expires=settings.CELERY_TASK_TIME_LIMIT)
@log_timing
def render_pdf_task(*args, **kwargs) -> dict:
    pdf, msgs = render.render_pdf(*args, **kwargs)
    return {
        'pdf': b64encode(pdf).decode() if pdf else None,
        'messages': msgs,
    }
