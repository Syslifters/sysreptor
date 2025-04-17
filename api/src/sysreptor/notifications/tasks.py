import json
import logging
from datetime import timedelta

import httpx
from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone

from sysreptor.api_utils.models import BackupLog
from sysreptor.notifications.models import NotificationType, UserNotification
from sysreptor.notifications.serializers import RemoteNotificationSpecSerializer
from sysreptor.tasks.models import TaskStatus, periodic_task
from sysreptor.users.models import PentestUser
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
        serializer = RemoteNotificationSpecSerializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        await sync_to_async(serializer.save)()
        return TaskStatus.SUCCESS
    except httpx.TransportError as ex:
        logging.warning(f'Failed to fetch notifications: {ex}. Check your internet connection.')
        return TaskStatus.FAILED


@periodic_task(id='create_notifications', schedule=timedelta(days=1))
async def create_notifications(task_info):
    if not await license.ais_professional():
        return

    # Notification when a backup is missing
    latest_backuplog = await BackupLog.objects.order_by('-created').afirst()
    if latest_backuplog and latest_backuplog.created < timezone.now() - timedelta(days=30):
        # Check if a notification already exists: do not multiple times
        existing_backup_notification = await UserNotification.objects \
            .filter(type=NotificationType.BACKUP_MISSING) \
            .filter(backuplog=latest_backuplog) \
            .afirst()
        if not existing_backup_notification:
            await sync_to_async(UserNotification.objects.create_for_users)(
                users=PentestUser.objects.only_active().filter(is_superuser=True),
                type=NotificationType.BACKUP_MISSING,
                created_by=None,
                backuplog=latest_backuplog,
            )

