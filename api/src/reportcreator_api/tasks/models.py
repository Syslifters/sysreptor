import dataclasses
from datetime import timedelta

from django.db import models
from django.utils import timezone

from reportcreator_api.tasks import querysets
from reportcreator_api.utils import license
from reportcreator_api.utils.models import BaseModel


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


@dataclasses.dataclass(frozen=True, eq=True)
class PeriodicTaskSpec:
    id: str
    schedule: timedelta
    func: callable
    retry: timedelta = timedelta(minutes=10)
    max_runtime: timedelta = timedelta(minutes=10)


@dataclasses.dataclass()
class PeriodicTaskInfo:
    spec: PeriodicTaskSpec
    model: PeriodicTask|None = None

    @property
    def id(self):
        return self.spec.id


@dataclasses.dataclass()
class PeriodicTaskRegistry:
    tasks: set[PeriodicTaskSpec] = dataclasses.field(default_factory=set)

    def register(self, task: PeriodicTaskSpec):
        if task in self.tasks:
            return  # already registered
        if any(t.id == task.id for t in self.tasks):
            raise ValueError(f'Task with id {task.id} already registered')
        self.tasks.add(task)

    def unregister(self, task: PeriodicTaskSpec):
        self.tasks.remove(task)


periodic_task_registry = PeriodicTaskRegistry()


def periodic_task(schedule: timedelta, id: str|None = None, retry: timedelta|None = None):
    def inner(func):
        periodic_task_registry.register(PeriodicTaskSpec(
            id=id or f'{func.__module__}.{func.__name__}',
            schedule=schedule,
            retry=retry or (schedule / 10),
            func=func,
        ))
        return func
    return inner


class LicenseActivationInfo(BaseModel):
    license_type = models.CharField(max_length=255, choices=license.LicenseType.choices)
    license_hash = models.CharField(max_length=255, null=True)
    last_activation_time = models.DateTimeField(null=True, blank=True)

    objects = querysets.LicenseActivationInfoManager()
