from django.db.models import signals
from django.dispatch import receiver

from sysreptor import signals as sysreptor_signals
from sysreptor.notifications.models import Notification, NotificationType, RemoteNotificationSpec
from sysreptor.pentests.models import (
    Comment,
    CommentAnswer,
    PentestFinding,
    PentestProject,
    ProjectMemberInfo,
    ProjectNotebookPage,
    ReportSection,
)
from sysreptor.users.models import PentestUser
from sysreptor.utils.models import disable_for_loaddata


@receiver(sysreptor_signals.post_create, sender=RemoteNotificationSpec)
@disable_for_loaddata
def remotenotificationspec_created(sender, instance, *args, **kwargs):
    RemoteNotificationSpec.objects.assign_to_users(instance)


@receiver(sysreptor_signals.post_create, sender=PentestUser)
@disable_for_loaddata
def user_created(sender, instance, *args, **kwargs):
    RemoteNotificationSpec.objects.assign_to_notifications(instance)


@receiver(sysreptor_signals.post_create, sender=ProjectMemberInfo)
@disable_for_loaddata
def notification_member_added(sender, instance, *args, **kwargs):
    created_by = Notification.objects.get_created_by()
    if instance.user != created_by and not Notification.objects.get_prevent_notifications():
        Notification.objects.create(
            type=NotificationType.MEMBER,
            user=instance.user,
            created_by=created_by,
            project=instance.project,
        )


@receiver(signals.post_save, sender=PentestFinding)
@receiver(signals.post_save, sender=ReportSection)
@receiver(signals.post_save, sender=ProjectNotebookPage)
@disable_for_loaddata
def notification_assigned(sender, instance, *args, **kwargs):
    created_by = Notification.objects.get_created_by()
    if (
        'assignee_id' in instance.changed_fields and
        instance.assignee_id and
        (not created_by or instance.assignee_id != created_by.id) and
        not Notification.objects.get_prevent_notifications()
    ):
        ref_field_name = {
            PentestFinding: 'finding',
            ReportSection: 'section',
            ProjectNotebookPage: 'note',
        }[sender]
        Notification.objects.create(
            type=NotificationType.ASSIGNED,
            user=instance.assignee,
            created_by=created_by,
            project=instance.project,
            **{ref_field_name: instance},
        )


@receiver(sysreptor_signals.post_finish, sender=PentestProject)
@disable_for_loaddata
def notification_finished(sender, instance, *args, **kwargs):
    Notification.objects.create_for_users(
        users=instance.members.all(),
        type=NotificationType.FINISHED,
        project=instance,
        skip_for_created_by=True,
    )


@receiver(signals.post_save, sender=Comment)
@receiver(signals.post_save, sender=CommentAnswer)
@disable_for_loaddata
def notification_comments(sender, instance, created, *args, **kwargs):
    if not ((created or 'text' in instance.changed_fields) and instance.text):
        return

    comment = instance if isinstance(instance, Comment) else instance.comment

    # Get users to notify
    notify_users = set()
    mentioned_usernames = set()
    if comment.finding and comment.finding.assignee:
        notify_users.add(comment.finding.assignee)
    if comment.section and comment.section.assignee:
        notify_users.add(comment.section.assignee)
    for c in [comment] + list(comment.answers.all()):
        # User who created the comment
        notify_users.add(c.user)

        # "@username" mentioned in text
        for m in Notification.MENTION_USERNAME_PATTERN.finditer(c.text):
            if username := m.group('username'):
                mentioned_usernames.add(username)
    notify_users.update(PentestUser.objects.filter(username__in=mentioned_usernames))

    Notification.objects.create_for_users(
        users=notify_users,
        type=NotificationType.COMMENTED,
        project=comment.project,
        finding=comment.finding,
        section=comment.section,
        comment=comment,
        created_by=instance.user,
        skip_for_created_by=True,
    )


@receiver(sysreptor_signals.post_archive, sender=PentestProject)
@disable_for_loaddata
def notification_archived(sender, instance, archive, *args, **kwargs):
    Notification.objects.create_for_users(
        users=instance.members.all(),
        type=NotificationType.ARCHIVED,
        additional_content={'project_name': instance.name},
        skip_for_created_by=False,
    )


@receiver(sysreptor_signals.post_delete, sender=PentestProject)
@disable_for_loaddata
def notification_deleted(sender, instance, *args, **kwargs):
    Notification.objects.create_for_users(
        users=instance.members.all(),
        type=NotificationType.DELETED,
        additional_content={'project_name': instance.name},
        skip_for_created_by=False,
    )
