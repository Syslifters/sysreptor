import json
import httpx
from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

from reportcreator_api.notifications.serializers import NotificationSpecSerializer
from reportcreator_api.utils import license


async def fetch_notifications_request():
    async with httpx.AsyncClient(timeout=10) as client:
        res = await client.post(
            url=settings.NOTIFICATION_IMPORT_URL,
            headers={'Content-Type': 'application/json'},
            data=json.dumps({
                'version': settings.VERSION,
                'license': await license.aget_license_info(),
                'instance_tags': settings.INSTANCE_TAGS,
            }, cls=DjangoJSONEncoder)
        )
        res.raise_for_status()
        return res.json()


async def fetch_notifications(task_info):
    if not settings.NOTIFICATION_IMPORT_URL:
        return

    data = await fetch_notifications_request()
    serializer = NotificationSpecSerializer(data=data, many=True)
    serializer.is_valid(raise_exception=True)
    await sync_to_async(serializer.save)()

