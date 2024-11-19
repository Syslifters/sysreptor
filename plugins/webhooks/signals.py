from django.dispatch import receiver
from reportcreator_api import signals as sysreptor_signals
from reportcreator_api.pentests.models import (
    PentestFinding,
    PentestProject,
)

from .utils import send_webhooks


@receiver(sysreptor_signals.post_create, sender=PentestProject)
async def on_project_created(sender, instance, *args, **kwargs):
    await send_webhooks('project_created', {'project_id': str(instance.id)})


@receiver(sysreptor_signals.post_finish, sender=PentestProject)
async def on_project_finished(sender, instance, *args, **kwargs):
    await send_webhooks('project_finished', {'project_id': str(instance.id)})


@receiver(sysreptor_signals.post_archive, sender=PentestProject)
async def on_project_archived(sender, project, archive, *args, **kwargs):
    await send_webhooks('project_archived', {'project_id': str(project.id), 'archive_id': str(archive.id)})


@receiver(sysreptor_signals.post_delete, sender=PentestProject)
async def on_project_deleted(sender, instance, *args, **kwargs):
    await send_webhooks('project_deleted', {'project_id': str(instance.id)})


@receiver(sysreptor_signals.post_create, sender=PentestFinding)
async def on_finding_created(sender, instance, *args, **kwargs):
    await send_webhooks('finding_created', {'project_id': str(instance.project_id), 'finding_id': str(instance.finding_id)})


@receiver(sysreptor_signals.post_delete, sender=PentestFinding)
async def on_finding_deleted(sender, instance, *args, **kwargs):
    await send_webhooks('finding_deleted', {'project_id': str(instance.project_id), 'finding_id': str(instance.finding_id)})

