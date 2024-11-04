import asyncio

from celery import shared_task
from django.conf import settings

from reportcreator_api.tasks.rendering import render


@shared_task(
    name='reportcreator.render_pdf',
    soft_time_limit=settings.PDF_RENDERING_TIME_LIMIT,
    time_limit=settings.PDF_RENDERING_TIME_LIMIT + 5,
    expires=settings.PDF_RENDERING_TIME_LIMIT + 5,
)
def render_pdf_task_celery(*args, **kwargs) -> dict:
    return asyncio.run(render_pdf_task_async(*args, **kwargs))


async def render_pdf_task_async(*args, **kwargs) -> dict:
    out = await render.render_pdf_impl(
        *args,
        should_compress_pdf=kwargs.pop('compress_pdf', False),
        **kwargs,
    )
    return out.to_dict()

