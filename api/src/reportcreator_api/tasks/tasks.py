import json
import logging
from datetime import timedelta

import httpx
from asgiref.sync import sync_to_async
from django.core.management import call_command
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import dateparse

from reportcreator_api.tasks.models import LicenseActivationInfo, TaskStatus, periodic_task
from reportcreator_api.utils import license


@periodic_task(id='clear_sessions', schedule=timedelta(days=1))
def clear_sessions(task_info):
    call_command('clearsessions')


async def activate_license_request(license_info):
    async with httpx.AsyncClient(timeout=10) as client:
        res = await client.post(
            url='https://portal.sysreptor.com/api/v1/licenses/activate/',
            headers={'Content-Type': 'application/json'},
            data=json.dumps(license_info, cls=DjangoJSONEncoder),
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
