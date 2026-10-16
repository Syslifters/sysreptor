from datetime import timedelta
from uuid import UUID, uuid4

from django.db.models import Exists, F, OuterRef, Q, Subquery
from django.utils import timezone
from langchain.messages import HumanMessage
from langgraph.types import Command

from sysreptor.ai.models import (
    AgentRunStatus,
    ChatThread,
    LangchainCheckpoint,
    LangchainCheckpointBlob,
    LangchainCheckpointWrite,
)
from sysreptor.ai.runs import HEARTBEAT_TTL_SECONDS, AgentRunWorker
from sysreptor.conf.taskiq import background_task
from sysreptor.tasks.models import PeriodicTaskInfo, periodic_task


@periodic_task(id='cleanup_stale_agent_runs', schedule=timedelta(days=1))
def cleanup_stale_agent_runs(task_info: PeriodicTaskInfo):
    cutoff = timezone.now() - timedelta(seconds=HEARTBEAT_TTL_SECONDS)
    ChatThread.objects \
        .filter(run_status=AgentRunStatus.RUNNING) \
        .filter(Q(run_heartbeat_at__isnull=True) | Q(run_heartbeat_at__lt=cutoff)) \
        .update(run_status=AgentRunStatus.ERROR)


@periodic_task(id='cleanup_old_langchain_checkpoints', schedule=timedelta(days=1))
def cleanup_old_langchain_checkpoints(task_info: PeriodicTaskInfo):
    older_than = timezone.now() - timedelta(hours=1)
    latest_ns_checkpoint = LangchainCheckpoint.objects \
        .filter(thread_id=OuterRef('thread_id')) \
        .filter(checkpoint_ns=OuterRef('checkpoint_ns')) \
        .order_by('-created') \
        .values('pk')[:1]
    checkpoints = LangchainCheckpoint.objects \
        .filter(created__lt=older_than) \
        .annotate(latest_ns_checkpoint_id=Subquery(latest_ns_checkpoint)) \
        .exclude(pk=F('latest_ns_checkpoint_id'))
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


@background_task('run_agent')
async def run_agent(
    thread_id: str,
    run_id: str,
    agent: str,
    model: str | None = None,
    message: str | None = None,
    resume: dict | None = None,
    context: dict | None = None,
):
    """
    Execute an agent run in the background, publishing events via channel layer.
    """
    thread_id = UUID(str(thread_id))
    run_id = UUID(str(run_id))

    thread = await ChatThread.objects \
        .filter(id=thread_id) \
        .filter(run_id=run_id) \
        .filter(run_status=AgentRunStatus.RUNNING) \
        .select_related('user', 'project') \
        .afirst()
    if not thread:
        # ChatThread deleted or run_id mismatched
        return

    if resume is not None:
        input_data = Command(resume=resume)
    else:
        input_data = {
            'messages': [HumanMessage(
                id=str(uuid4()) if message else None,
                content=message or '',
            )],
        }

    await AgentRunWorker(
        thread,
        agent=agent,
        model=model,
        input_data=input_data,
        context=context,
    ).run()
