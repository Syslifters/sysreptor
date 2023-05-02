from base64 import b64encode
from celery import shared_task

from reportcreator_api.utils.logging import log_timing
from reportcreator_api.tasks.rendering import render


@shared_task(name='reportcreator.render_pdf', expires=3 * 60, time_limit=3 * 60)
@log_timing
def render_pdf_task(*args, **kwargs) -> dict:
    pdf, msgs = render.render_pdf(*args, **kwargs)
    return {
        'pdf': b64encode(pdf).decode() if pdf else None,
        'messages': msgs,
    }
