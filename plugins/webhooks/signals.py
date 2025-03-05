from django.dispatch import receiver
from reportcreator_api import signals as sysreptor_signals
from reportcreator_api.pentests.models import (
    PentestFinding,
    PentestProject,
    ReportSection,
)

from .models import WebhookEventType
from .utils import send_webhooks


@receiver(sysreptor_signals.post_create, sender=PentestProject)
async def on_project_created(sender, instance, *args, **kwargs):
    await send_webhooks(WebhookEventType.PROJECT_CREATED, {'project_id': str(instance.id)})


@receiver(sysreptor_signals.post_finish, sender=PentestProject)
async def on_project_finished(sender, instance, *args, **kwargs):
    await send_webhooks(WebhookEventType.PROJECT_FINISHED, {'project_id': str(instance.id)})


@receiver(sysreptor_signals.post_archive, sender=PentestProject)
async def on_project_archived(sender, instance, archive, *args, **kwargs):
    await send_webhooks(WebhookEventType.PROJECT_ARCHIVED, {'project_id': str(instance.id), 'archive_id': str(archive.id)})


@receiver(sysreptor_signals.post_delete, sender=PentestProject)
async def on_project_deleted(sender, instance, *args, **kwargs):
    await send_webhooks(WebhookEventType.PROJECT_DELETED, {'project_id': str(instance.id)})


@receiver(sysreptor_signals.post_create, sender=PentestFinding)
async def on_finding_created(sender, instance, *args, **kwargs):
    await send_webhooks(WebhookEventType.FINDING_CREATED, {'project_id': str(instance.project_id), 'finding_id': str(instance.finding_id)})


@receiver(sysreptor_signals.post_delete, sender=PentestFinding)
async def on_finding_deleted(sender, instance, *args, **kwargs):
    await send_webhooks(WebhookEventType.FINDING_DELETED, {'project_id': str(instance.project_id), 'finding_id': str(instance.finding_id)})


@receiver(sysreptor_signals.post_update, sender=PentestFinding)
async def on_finding_updated(sender, instance, changed_fields, *args, **kwargs):
    changed_fields -= {'created', 'updated', 'order', 'custom_fields', 'data'}
    if changed_fields:
        await send_webhooks(WebhookEventType.FINDING_UPDATED, {'project_id': str(instance.project_id), 'finding_id': str(instance.finding_id), 'fields': changed_fields})


@receiver(sysreptor_signals.post_update, sender=ReportSection)
async def on_section_updated(sender, instance, changed_fields, *args, **kwargs):
    changed_fields -= {'created', 'updated', 'custom_fields', 'data'}
    if changed_fields:
        await send_webhooks(WebhookEventType.SECTION_UPDATED, {'project_id': str(instance.project_id), 'section_id': str(instance.section_id), 'fields': changed_fields})
