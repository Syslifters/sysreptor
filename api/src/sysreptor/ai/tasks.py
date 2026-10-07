from datetime import timedelta

from django.db.models import Exists, F, OuterRef, Subquery
from django.utils import timezone

from sysreptor.ai.models import LangchainCheckpoint, LangchainCheckpointBlob, LangchainCheckpointWrite
from sysreptor.tasks.models import PeriodicTaskInfo, periodic_task


@periodic_task(id='cleanup_old_langchain_checkpoints', schedule=timedelta(days=1))
def cleanup_old_langchain_checkpoints(task_info: PeriodicTaskInfo):
    older_than = timezone.now() - timedelta(hours=1)
    latest_thread_checkpoint = LangchainCheckpoint.objects \
        .filter(thread_id=OuterRef('thread_id')) \
        .order_by('-created') \
        .values('pk')[:1]
    checkpoints = LangchainCheckpoint.objects \
        .filter(created__lt=older_than) \
        .annotate(latest_thread_checkpoint_id=Subquery(latest_thread_checkpoint)) \
        .exclude(pk=F('latest_thread_checkpoint_id'))
    if last_run := task_info.model.last_success:
        last_run = min(last_run, older_than - timedelta(days=1)) - timedelta(hours=1)
        checkpoints = checkpoints.filter(created__gt=last_run)

    stale = list(checkpoints.only('pk', 'thread_id', 'checkpoint_ns', 'checkpoint_id'))
    if not stale:
        return

    # Delete checkpoints and writes
    stale_pks = [row.pk for row in stale]
    thread_ids = {row.thread_id for row in stale}
    stale_checkpoint = LangchainCheckpoint.objects.filter(pk__in=stale_pks)
    LangchainCheckpointWrite.objects \
        .filter(Exists(stale_checkpoint.filter(
            thread_id=OuterRef('thread_id'),
            checkpoint_ns=OuterRef('checkpoint_ns'),
            checkpoint_id=OuterRef('checkpoint_id'),
        ))) \
        .delete()
    stale_checkpoint.delete()

    # Delete unreferenced blobs
    referenced: set[tuple] = set()
    existing_checkpoints = LangchainCheckpoint.objects \
        .filter(thread_id__in=thread_ids) \
        .values_list('thread_id', 'checkpoint_ns', 'checkpoint')
    for thread_id, checkpoint_ns, checkpoint in existing_checkpoints:
        for channel, version in ((checkpoint or {}).get('channel_versions') or {}).items():
            referenced.add((thread_id, checkpoint_ns or '', channel, str(version)))

    stale_blob_pks = []
    existing_blobs = LangchainCheckpointBlob.objects \
        .filter(thread_id__in=thread_ids) \
        .values_list('pk', 'thread_id', 'checkpoint_ns', 'channel', 'version')
    for pk, thread_id, checkpoint_ns, channel, version in existing_blobs:
        if (thread_id, checkpoint_ns or '', channel, str(version)) not in referenced:
            stale_blob_pks.append(pk)
    if stale_blob_pks:
        LangchainCheckpointBlob.objects.filter(pk__in=stale_blob_pks).delete()
