import logging
from datetime import timedelta

import elasticapm
from asgiref.sync import iscoroutinefunction, sync_to_async
from django.db import IntegrityError, models
from django.utils import timezone

log = logging.getLogger(__name__)


class PeriodicTaskQuerySet(models.QuerySet):
    async def get_pending_tasks(self):
        from reportcreator_api.tasks.models import PeriodicTaskInfo, TaskStatus, periodic_task_registry
        task_specs = {t.id: t for t in periodic_task_registry.tasks}
        task_models = {t.id: t async for t in self.filter(id__in=task_specs.keys())}
        out = []
        for t_id, spec in task_specs.items():
            model = task_models.get(t_id)
            # Remove non-pending tasks
            if model and (
                (model.status == TaskStatus.RUNNING and model.started > timezone.now() - timedelta(minutes=10)) or \
                (model.status == TaskStatus.FAILED and model.started > timezone.now() - timedelta(minutes=10)) or \
                (model.status == TaskStatus.SUCCESS and model.started > timezone.now() - spec.schedule)
            ):
                continue
            out.append(PeriodicTaskInfo(spec=spec, model=model))
        return out


class PeriodicTaskManager(models.Manager.from_queryset(PeriodicTaskQuerySet)):
    async def run_task(self, task_info):
        from reportcreator_api.tasks.models import PeriodicTask, PeriodicTaskInfo, TaskStatus
        task_info: PeriodicTaskInfo

        # Lock task
        if task_info.model:
            started = timezone.now()
            res = await PeriodicTask.objects \
                .filter(id=task_info.id) \
                .filter(status=task_info.model.status) \
                .filter(started=task_info.model.started) \
                .filter(completed=task_info.model.completed) \
                .aupdate(status=TaskStatus.RUNNING, started=started, completed=None)
            if res != 1:
                return
            task_info.model.status = TaskStatus.RUNNING
            task_info.model.started = started
            task_info.model.completed = None
        else:
            try:
                task_info.model = await PeriodicTask.objects.acreate(
                    id=task_info.id,
                    status=TaskStatus.RUNNING,
                    started=timezone.now(),
                    completed=None,
                )
            except IntegrityError:
                return

        # Execute task
        log.info(f'Starting periodic task "{task_info.id}"')
        try:
            async with elasticapm.async_capture_span(task_info.id):
                if iscoroutinefunction(task_info.spec.func):
                    await task_info.spec.func(task_info)
                else:
                    await sync_to_async(task_info.spec.func)(task_info)
            task_info.model.status = TaskStatus.SUCCESS
            task_info.model.last_success = timezone.now()
            task_info.model.completed = task_info.model.last_success
        except Exception:
            logging.exception(f'Error while running periodic task "{task_info.id}"')
            task_info.model.status = TaskStatus.FAILED
            task_info.model.completed = timezone.now()
        log.info(f'Completed periodic task "{task_info.id}" with status "{task_info.model.status}"')

        await task_info.model.asave()

    async def run_all_pending_tasks(self):
        for t in await self.get_pending_tasks():
            await self.run_task(t)
