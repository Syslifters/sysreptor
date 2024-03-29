from django.db import models

from reportcreator_api.notifications import querysets
from reportcreator_api.users.models import PentestUser
from reportcreator_api.utils.models import BaseModel


class NotificationSpec(BaseModel):
    """
    Specification for a notification that gets assigned to users.
    """
    active_until = models.DateField(null=True, blank=True, db_index=True)
    user_conditions = models.JSONField(default=dict, blank=True)
    visible_for_days = models.IntegerField(null=True, blank=True)

    title = models.CharField(max_length=255)
    text = models.TextField()
    link_url = models.TextField(null=True, blank=True)

    objects = querysets.NotificationSpecManager()

    def __str__(self) -> str:
        return self.title


class UserNotification(BaseModel):
    """
    Notification assigned to a specific user. Can marked as read.
    """
    user = models.ForeignKey(to=PentestUser, on_delete=models.CASCADE, related_name='notifications')
    notification = models.ForeignKey(to=NotificationSpec, on_delete=models.CASCADE)

    visible_until = models.DateTimeField(null=True, blank=True, )
    read = models.BooleanField(default=False, db_index=True)

    objects = models.Manager.from_queryset(querysets.UserNotificationQuerySet)()

    class Meta:
        unique_together = [('user', 'notification')]

