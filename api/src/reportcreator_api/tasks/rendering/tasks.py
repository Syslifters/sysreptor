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
        'messages': [m.to_dict() for m in msgs],
    }


# TODO: render MD to HTML
# * [x] flow:
#   * [x] serialize project data to dict
#   * [x] collect all markdown fields to a single list
#   * [x] send list of markdown fields to rendering task
#   * [x] render markdown fields via JS inside chromium
#   * [x] render with full Vue support (also evaluate Vue template language inside markdown)
#   * [x] return rendered HTML, do not render to PDF
# * [x] api
#   * [x] rate limit: "pdf"
#   * [x] view: POST /api/v1/projects/<id>/md2html/ -> 200 JSON; 400 messages
#   * [x] async view
# * [x] OpenAPI schema warnings
# * [ ] tests:
#   * [x] test_api
#   * [ ] test_rendering: test md2html rendering: md in finding, section

