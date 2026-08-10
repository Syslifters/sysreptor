from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models import signals
from django.dispatch import receiver

from sysreptor import signals as sysreptor_signals
from sysreptor.api_utils.models import BackupLog, BackupLogType
from sysreptor.audit.models import AuditLogTypes
from sysreptor.pentests.models import PentestProject, ProjectMemberInfo, ShareInfo
from sysreptor.users.models import APIToken, AuthIdentity, MFAMethod, PentestUser
from sysreptor.utils.audit import audit_log
from sysreptor.utils.models import disable_for_loaddata
from sysreptor.utils.utils import copy_keys


def _changes(instance, fields):
    def ser(v):
        if hasattr(v, 'pk'):
            return str(v.pk)
        if isinstance(v, list):
            return [str(x.pk) if hasattr(x, 'pk') else x for x in v]
        return v
    return {
        f: [ser(old), ser(new)]
        for f in instance.changed_fields if f in fields
        for old, new in [instance.get_field_diff(f)]
    }


@receiver(user_logged_in)
def audit_login(sender, request, user, **kwargs):
    if not user:
        return
    audit_log(
        type=AuditLogTypes.LOGIN_SUCCESS,
        user=user,
        related=user,
        data=getattr(request, '_audit_login', None),
    )


@receiver(user_logged_out)
def audit_logout(sender, request, user, **kwargs):
    if user:
        audit_log(type=AuditLogTypes.LOGOUT, user=user, related=user)


@receiver(signals.post_save, sender=PentestUser)
@disable_for_loaddata
def audit_user_save(sender, instance, created, **kwargs):
    USER_SENSITIVE_FIELDS = {'username', 'email', 'is_active', 'can_login_local'}
    USER_PERMISSON_FIELDS = {
        'is_superuser', 'is_system_user', 'is_project_admin', 'is_user_manager',
        'is_designer', 'is_template_editor', 'is_guest', 'is_global_archiver',
    }
    if created:
        audit_log(type=AuditLogTypes.USER_CREATED, related=instance, data=copy_keys(instance, USER_SENSITIVE_FIELDS | USER_PERMISSON_FIELDS))
        return
    if 'password' in instance.changed_fields:
        audit_log(type=AuditLogTypes.PASSWORD_CHANGED, related=instance)
    if changes := _changes(instance, USER_SENSITIVE_FIELDS):
        audit_log(type=AuditLogTypes.USER_UPDATED, related=instance, data={'changes': changes})
    if changes := _changes(instance, USER_PERMISSON_FIELDS):
        audit_log(type=AuditLogTypes.USER_PERMISSIONS_UPDATED, related=instance, data={'changes': changes})


@receiver(sysreptor_signals.post_delete, sender=PentestUser)
def audit_user_delete(sender, instance, **kwargs):
    audit_log(type=AuditLogTypes.USER_DELETED, related=instance)


@receiver(sysreptor_signals.post_create, sender=MFAMethod)
def audit_mfa_create(sender, instance, **kwargs):
    audit_log(type=AuditLogTypes.MFA_CREATED, related=instance.user, data={
        'mfa': {
            'id': str(instance.id),
            'method_type': instance.method_type,
            'name': instance.name,
        },
    })


@receiver(sysreptor_signals.post_delete, sender=MFAMethod)
def audit_mfa_delete(sender, instance, origin=None, **kwargs):
    if isinstance(origin, PentestUser):
        return
    audit_log(type=AuditLogTypes.MFA_DELETED, related=instance.user, data={
        'mfa': {
            'id': str(instance.id),
            'method_type': instance.method_type,
            'name': instance.name,
        },
    })


@receiver(sysreptor_signals.post_create, sender=APIToken)
def audit_api_token_create(sender, instance, **kwargs):
    audit_log(type=AuditLogTypes.API_TOKEN_CREATED, related=instance.user, data={
        'api_token': {
            'id': str(instance.id),
            'name': instance.name,
            'expire_date': instance.expire_date,
            'admin_permissions_enabled': instance.admin_permissions_enabled,
        },
    })


@receiver(sysreptor_signals.post_create, sender=AuthIdentity)
@disable_for_loaddata
def audit_auth_identity_create(sender, instance, **kwargs):
    audit_log(type=AuditLogTypes.AUTH_IDENTITY_CREATED, related=instance.user, data={
        'auth_identity': {
            'provider': instance.provider,
            'identifier': instance.identifier,
        },
    })


@receiver(sysreptor_signals.post_delete, sender=AuthIdentity)
def audit_auth_identity_delete(sender, instance, origin=None, **kwargs):
    if isinstance(origin, PentestUser):
        return
    audit_log(type=AuditLogTypes.AUTH_IDENTITY_DELETED, related=instance.user, data={
        'auth_identity': {
            'provider': instance.provider,
            'identifier': instance.identifier,
        },
    })


@receiver(sysreptor_signals.post_create, sender=ProjectMemberInfo)
def audit_project_member_create(sender, instance, **kwargs):
    audit_log(type=AuditLogTypes.PROJECT_MEMBER_ADDED, related=instance.project, data={
        'member': {
            'id': str(instance.user.id),
            'username': instance.user.username,
        },
        'project': {
            'id': str(instance.project.id),
            'name': instance.project.name,
        },
    })


@receiver(sysreptor_signals.post_delete, sender=ProjectMemberInfo)
def audit_project_member_delete(sender, instance, origin=None, **kwargs):
    if isinstance(origin, PentestProject | PentestUser):
        return
    audit_log(type=AuditLogTypes.PROJECT_MEMBER_REMOVED, related=instance.project, data={
        'member': {
            'id': str(instance.user.id),
            'username': instance.user.username,
        },
        'project': {
            'id': str(instance.project.id),
            'name': instance.project.name,
        },
    })


@receiver(sysreptor_signals.post_create, sender=BackupLog)
def audit_backup_log(sender, instance, **kwargs):
    if instance.type not in {BackupLogType.BACKUP_STARTED.value, BackupLogType.RESTORE.value}:
        return
    audit_log(type=instance.type, user=instance.user, related=instance)


@receiver(sysreptor_signals.post_create, sender=ShareInfo)
def audit_note_share_create(sender, instance, **kwargs):
    data = {
        'share': {
            'id': str(instance.id),
            'type': instance.share_type,
            'expire_date': instance.expire_date,
            'permissions_write': instance.permissions_write,
            'password_protected': bool(instance.password),
        },
    }
    if instance.projectnote_id:
        note = instance.projectnote
        data |= {
            'note': {
                'id': str(note.note_id),
                'title': note.title,
            },
            'project': {
                'id': str(note.project_id),
                'name': note.project.name,
            },
        }
    elif instance.usernote_id:
        note = instance.usernote
        data |= {
            'note': {
                'id': str(note.note_id),
                'title': note.title,
            },
            'user': {
                'id': str(note.user_id),
                'username': note.user.username,
            },
        }
    else:
        return
    audit_log(type=AuditLogTypes.NOTE_SHARE_CREATED, user=instance.shared_by, related=note, data=data)
