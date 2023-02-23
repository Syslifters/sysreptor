from django.db import models
from django.utils import timezone

from reportcreator_api.utils.models import BaseModel
from reportcreator_api.tasks import querysets


class TaskStatus(models.TextChoices):
    RUNNING = 'running', 'Running'
    SUCCESS = 'success', 'Success'
    FAILED = 'failed', 'Failed'


class PeriodicTask(BaseModel):
    id = models.CharField(max_length=255, primary_key=True)
    status = models.CharField(max_length=10, choices=TaskStatus.choices, default=TaskStatus.RUNNING)
    started = models.DateTimeField(default=timezone.now)
    completed = models.DateTimeField(null=True, blank=True)
    last_success = models.DateTimeField(null=True, blank=True)

    objects = querysets.PeriodicTaskManager()
