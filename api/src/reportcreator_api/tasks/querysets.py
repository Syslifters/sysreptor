import logging
import elasticapm
from asgiref.sync import sync_to_async, iscoroutinefunction
from datetime import timedelta
from django.db import models, IntegrityError
from django.db.models.functions import Rank
from django.conf import settings
from django.utils import timezone
from django.utils.module_loading import import_string

log = logging.getLogger(__name__)


class PeriodicTaskQuerySet(models.QuerySet):
    def get_pending_tasks(self):
        from reportcreator_api.tasks.models import TaskStatus
        pending_tasks = {t['id']: t.copy() for t in settings.PERIODIC_TASKS}
        for t in self.filter(id__in=pending_tasks.keys()):
            pending_tasks[t.id]['model'] = t
            # Remove non-pending tasks
            if (t.status == TaskStatus.RUNNING and t.started > timezone.now() - timedelta(minutes=10)) or \
               (t.status == TaskStatus.FAILED and t.started > timezone.now() - timedelta(minutes=10)) or \
               (t.status == TaskStatus.SUCCESS and t.started > timezone.now() - pending_tasks[t.id]['schedule']):
               del pending_tasks[t.id]
        return pending_tasks.values()


class PeriodicTaskManager(models.Manager.from_queryset(PeriodicTaskQuerySet)):
    async def run_task(self, task_info):
        from reportcreator_api.tasks.models import PeriodicTask, TaskStatus

        # Lock task
        if task_info.get('model'):
            started = timezone.now()
            res = await PeriodicTask.objects \
                .filter(id=task_info['id']) \
                .filter(status=task_info['model'].status) \
                .filter(started=task_info['model'].started) \
                .filter(completed=task_info['model'].completed) \
                .aupdate(status=TaskStatus.RUNNING, started=started, completed=None)
            if res != 1:
                return
            task_info['model'].status = TaskStatus.RUNNING
            task_info['model'].started = started
            task_info['model'].completed = None
        else:
            try:
                task_info['model'] = await PeriodicTask.objects.acreate(
                    id=task_info['id'], 
                    status=TaskStatus.RUNNING, 
                    started=timezone.now(), 
                    completed=None
                )
            except IntegrityError:
                return

        # Execute task
        log.info(f'Starting periodic task "{task_info["id"]}"')
        try:
            task_fn = import_string(task_info['task'])
            async with elasticapm.async_capture_span(task_info['id']):
                if iscoroutinefunction(task_fn):
                    await task_fn(task_info)
                else:
                    await sync_to_async(task_fn)(task_info)
            task_info['model'].status = TaskStatus.SUCCESS
            task_info['model'].last_success = timezone.now()
            task_info['model'].completed = task_info['model'].last_success
        except Exception:
            logging.exception(f'Error while running periodic task "{task_info["id"]}"')
            task_info['model'].status = TaskStatus.FAILED
            task_info['model'].completed = timezone.now()
        log.info(f'Completed periodic task "{task_info["id"]}" with status "{task_info["model"].status}"')
        
        await task_info['model'].asave()

    async def run_all_pending_tasks(self):
        for t in await sync_to_async(self.get_pending_tasks)():
            await self.run_task(t)
