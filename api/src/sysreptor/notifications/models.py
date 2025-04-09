import re
from datetime import datetime, timedelta

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils import timezone

from sysreptor.notifications import querysets
from sysreptor.users.models import PentestUser
from sysreptor.utils.models import BaseModel
from sysreptor.utils.utils import copy_keys, datetime_from_date


class RemoteNotificationSpec(BaseModel):
    """
    Specification for a remote notification that gets assigned to users.
    """
    active_until = models.DateField(null=True, blank=True, db_index=True)
    user_conditions = models.JSONField(default=dict, blank=True)
    visible_for_days = models.IntegerField(null=True, blank=True)

    title = models.CharField(max_length=255)
    text = models.TextField()
    link_url = models.TextField(null=True, blank=True)

    objects = querysets.RemoteNotificationSpecManager()

    def __str__(self) -> str:
        return self.title

    @property
    def visible_until(self) -> datetime|None:
        out = None
        if self.visible_for_days:
            out = timezone.now() + timedelta(days=self.visible_for_days)
        if self.active_until:
            active_until_datetime = datetime_from_date(self.active_until)
            if not out or active_until_datetime < out:
                out = active_until_datetime
        return out


class NotificationType(models.TextChoices):
    REMOTE = 'remote'

    MEMBER_ADDED = 'member_added'
    FINISHED = 'finished'
    ARCHIVED = 'archived'
    DELETED = 'deleted'
    COMMENTED = 'commented'
    ASSIGNED = 'assigned'
    BACKUP_MISSING = 'backup_missing'


class NotificationStatus(models.TextChoices):
    OPEN = 'open'
    RESOLVED = 'resolved'


class Notification(BaseModel):
    """
    Notification assigned to a specific user. Can marked as resolved.
    """

    MENTION_USERNAME_PATTERN = re.compile(r'(^|(?<=\s))@(?P<username>[\w\-.@]*\w)((?=[\s.:,;!?])|$)')

    user = models.ForeignKey(to=PentestUser, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=50, choices=NotificationType.choices)
    status = models.CharField(max_length=10, choices=NotificationStatus.choices, default=NotificationStatus.OPEN)
    visible_until = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(to=PentestUser, on_delete=models.SET_NULL, null=True, blank=True)  # TODO: find better name for field
    additional_content = models.JSONField(encoder=DjangoJSONEncoder, default=dict)

    # Links to related objects
    remotenotificationspec = models.ForeignKey(to=RemoteNotificationSpec, on_delete=models.CASCADE, null=True, blank=True)
    project = models.ForeignKey(to='pentests.PentestProject', on_delete=models.CASCADE, null=True, blank=True)
    finding = models.ForeignKey(to='pentests.PentestFinding', on_delete=models.CASCADE, null=True, blank=True)
    section = models.ForeignKey(to='pentests.ReportSection', on_delete=models.CASCADE, null=True, blank=True)
    note = models.ForeignKey(to='pentests.ProjectNotebookPage', on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(to='pentests.Comment', on_delete=models.CASCADE, null=True, blank=True)

    objects = querysets.NotificationManager()

    @property
    def content(self) -> dict:
        reference_content = {}
        if self.project_id:
            reference_content |= {'project_id': self.project.id}
        elif self.finding_id:
            reference_content |= {
                'finding_id': self.finding.finding_id,
                'project_id': self.finding.project_id,
            }
        elif self.section_id:
            reference_content |= {
                'section_id': self.section.section_id,
                'project_id': self.section.project_id,
            }
        elif self.note_id:
            reference_content |= {
                'note_id': self.note.note_id,
                'project_id': self.note.project_id,
            }
        elif self.comment_id:
            reference_content |= {
                'comment_id': self.comment.comment_id,
                'project_id': self.comment.project_id,
            }
            if self.comment.finding_id:
                reference_content |= {'finding_id': self.comment.finding.finding_id}
            elif self.comment.section_id:
                reference_content |= {'section_id': self.comment.section.section_id}
        elif self.remotenotificationspec_id:
            reference_content |= copy_keys(self.remotenotificationspec, ['title', 'text', 'link_url'])
        return self.additional_content | reference_content

