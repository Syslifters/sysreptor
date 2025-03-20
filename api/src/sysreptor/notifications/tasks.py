import json
import logging
from datetime import timedelta

import httpx
from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

from sysreptor.notifications.serializers import NotificationSpecSerializer
from sysreptor.tasks.models import TaskStatus, periodic_task
from sysreptor.utils import license


async def fetch_notifications_request():
    async with httpx.AsyncClient(timeout=10) as client:
        res = await client.post(
            url=settings.NOTIFICATION_IMPORT_URL,
            headers={'Content-Type': 'application/json'},
            data=json.dumps({
                'version': settings.VERSION,
                'license': await license.aget_license_info(),
                'instance_tags': settings.INSTANCE_TAGS,
            }, cls=DjangoJSONEncoder),
        )
        res.raise_for_status()
        return res.json()


@periodic_task(id='fetch_notifications', schedule=timedelta(days=1))
async def fetch_notifications(task_info):
    if not settings.NOTIFICATION_IMPORT_URL:
        return

    try:
        data = await fetch_notifications_request()
        serializer = NotificationSpecSerializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        await sync_to_async(serializer.save)()
        return TaskStatus.SUCCESS
    except httpx.TransportError as ex:
        logging.warning(f'Failed to fetch notifications: {ex}. Check your internet connection.')
        return TaskStatus.FAILED

