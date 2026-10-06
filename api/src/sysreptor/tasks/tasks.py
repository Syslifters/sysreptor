import json
import logging
from datetime import timedelta

import httpx
from asgiref.sync import sync_to_async
from django.core.management import call_command
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import dateparse

from sysreptor.conf.taskiq import background_task
from sysreptor.tasks.models import (
    LicenseActivationInfo,
    PeriodicTask,
    PeriodicTaskInfo,
    TaskStatus,
    periodic_task,
    periodic_task_registry,
)
from sysreptor.utils import license


@background_task('execute_periodic_task')
async def execute_periodic_task(task_id: str):
    from sysreptor.tasks.querysets import is_task_pending

    spec = next((t for t in periodic_task_registry.tasks if t.id == task_id), None)
    if not spec:
        logging.warning(f'Unknown periodic task "{task_id}"')
        return

    model = await PeriodicTask.objects.filter(id=task_id).afirst()
    # Drop stale duplicate messages that arrive after another worker already ran.
    if not is_task_pending(model, spec):
        return
    await PeriodicTask.objects.run_task(PeriodicTaskInfo(spec=spec, model=model))


@periodic_task(id='clear_sessions', schedule=timedelta(days=1))
def clear_sessions(task_info):
    call_command('clearsessions')


async def activate_license_request(license_info):
    async with httpx.AsyncClient(timeout=10) as client:
        res = await client.post(
            url='https://sysreptor.com/api/v1/licenses/activate/',
            headers={'Content-Type': 'application/json'},
            content=json.dumps(license_info, cls=DjangoJSONEncoder).encode(),
        )
        res.raise_for_status()
        return res.json()


@periodic_task(id='activate_license', schedule=timedelta(days=1))
async def activate_license(task_info):
    activation_info = await sync_to_async(LicenseActivationInfo.objects.current)()
    if not await license.ais_professional():
        return TaskStatus.SUCCESS

    try:
        res = await activate_license_request(await license.aget_license_info())
        if res.get('status') == 'ok':
            try:
                activation_info.last_activation_time = dateparse.parse_datetime(res.get('license_info', {}).get('last_activation_time'))
            except (TypeError, ValueError):
                activation_info.last_activation_time = None
            await activation_info.asave()
    except httpx.TransportError as ex:
        logging.warning(f'Failed to activate license: {ex}. Check your internet connection.')
        return TaskStatus.FAILED
