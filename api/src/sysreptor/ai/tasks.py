from datetime import timedelta

from django.db.models import F, OuterRef, Subquery
from django.utils import timezone

from sysreptor.ai.models import LangchainCheckpoint
from sysreptor.tasks.models import PeriodicTaskInfo, periodic_task


@periodic_task(id='cleanup_old_langchain_checkpoints', schedule=timedelta(days=1))
async def cleanup_old_langchain_checkpoints(task_info: PeriodicTaskInfo):
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

    await checkpoints.adelete()
