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


def _data(object_repr, owned=None, **extra):
    data = {'object_repr': object_repr, **extra}
    if owned is not None:
        data |= {'user_id': str(owned.user_id), 'username': owned.user.username}
    return data


@receiver(user_logged_in)
def audit_login(sender, request, user, **kwargs):
    if user:
        audit_log(type=AuditLogTypes.LOGIN_SUCCESS, user=user, related=user, data=_data(user.username))


@receiver(user_logged_out)
def audit_logout(sender, request, user, **kwargs):
    if user:
        audit_log(type=AuditLogTypes.LOGOUT, user=user, related=user, data=_data(user.username))


@receiver(signals.post_save, sender=PentestUser)
@disable_for_loaddata
def audit_user_save(sender, instance, created, **kwargs):
    data = _data(instance.username)
    if created:
        audit_log(type=AuditLogTypes.USER_CREATED, related=instance, data=data)
        return
    if 'password' in instance.changed_fields:
        audit_log(type=AuditLogTypes.PASSWORD_CHANGED, related=instance, data=data)
    if changes := _changes(instance, {'username', 'email', 'is_active', 'can_login_local'}):
        audit_log(type=AuditLogTypes.USER_UPDATED, related=instance, data=data | {'changes': changes})
    if changes := _changes(instance, {
        'is_superuser', 'is_system_user', 'is_project_admin', 'is_user_manager',
        'is_designer', 'is_template_editor', 'is_guest', 'is_global_archiver',
    }):
        audit_log(type=AuditLogTypes.USER_PERMISSIONS_UPDATED, related=instance, data=data | {'changes': changes})


@receiver(sysreptor_signals.post_delete, sender=PentestUser)
def audit_user_delete(sender, instance, **kwargs):
    audit_log(type=AuditLogTypes.USER_DELETED, related=instance, data=_data(instance.username))


@receiver(sysreptor_signals.post_create, sender=MFAMethod)
def audit_mfa_create(sender, instance, **kwargs):
    audit_log(type=AuditLogTypes.MFA_CREATED, related=instance, data=_data(
        f'{instance.method_type}: {instance.name}', owned=instance, method_type=instance.method_type))


@receiver(sysreptor_signals.post_delete, sender=MFAMethod)
def audit_mfa_delete(sender, instance, origin=None, **kwargs):
    if isinstance(origin, PentestUser):
        return
    audit_log(type=AuditLogTypes.MFA_DELETED, related=instance, data=_data(
        f'{instance.method_type}: {instance.name}', owned=instance, method_type=instance.method_type))


@receiver(sysreptor_signals.post_create, sender=APIToken)
def audit_api_token_create(sender, instance, **kwargs):
    audit_log(type=AuditLogTypes.API_TOKEN_CREATED, related=instance, data=_data(
        instance.name, owned=instance,
        expire_date=instance.expire_date.isoformat() if instance.expire_date else None,
        admin_permissions_enabled=instance.admin_permissions_enabled))


@receiver(sysreptor_signals.post_create, sender=AuthIdentity)
@disable_for_loaddata
def audit_auth_identity_save(sender, instance, **kwargs):
    audit_log(type=AuditLogTypes.AUTH_IDENTITY_CREATED, related=instance.user, data=_data(
        f'{instance.provider}: {instance.identifier}', owned=instance,
        provider=instance.provider, identifier=instance.identifier))


@receiver(sysreptor_signals.post_delete, sender=AuthIdentity)
def audit_auth_identity_delete(sender, instance, origin=None, **kwargs):
    if isinstance(origin, PentestUser):
        return
    audit_log(type=AuditLogTypes.AUTH_IDENTITY_DELETED, related=instance.user, data=_data(
        f'{instance.provider}: {instance.identifier}', owned=instance,
        provider=instance.provider, identifier=instance.identifier))


@receiver(sysreptor_signals.post_create, sender=ProjectMemberInfo)
def audit_project_member_create(sender, instance, **kwargs):
    audit_log(type=AuditLogTypes.PROJECT_MEMBER_ADDED, related=instance.project, data=_data(
        f'{instance.user.username} @ {instance.project.name}', owned=instance,
        project_id=str(instance.project_id), project_name=instance.project.name, roles=list(instance.roles)))


@receiver(sysreptor_signals.post_delete, sender=ProjectMemberInfo)
def audit_project_member_delete(sender, instance, origin=None, **kwargs):
    if isinstance(origin, PentestProject | PentestUser):
        return
    audit_log(type=AuditLogTypes.PROJECT_MEMBER_REMOVED, related=instance.project, data=_data(
        f'{instance.user.username} @ {instance.project.name}', owned=instance,
        project_id=str(instance.project_id), project_name=instance.project.name, roles=list(instance.roles)))


@receiver(sysreptor_signals.post_create, sender=BackupLog)
def audit_backup_log(sender, instance, **kwargs):
    if instance.type not in {BackupLogType.BACKUP_STARTED.value, BackupLogType.RESTORE.value}:
        return
    audit_log(type=instance.type, user=instance.user, related=instance, data=_data(instance.type))


@receiver(sysreptor_signals.post_create, sender=ShareInfo)
def audit_note_share_create(sender, instance, **kwargs):
    data = _data(str(instance.id), share_type=instance.share_type, expire_date=instance.expire_date.isoformat(),
                 permissions_write=instance.permissions_write, password_protected=bool(instance.password))
    if instance.projectnote_id:
        note = instance.projectnote
        data |= {
            'note_id': str(note.note_id),
            'note_title': note.title,
            'project_id': str(note.project_id),
            'project_name': note.project.name,
        }
    elif instance.usernote_id:
        note = instance.usernote
        data |= {
            'note_id': str(note.note_id),
            'note_title': note.title,
            'note_user_id': str(note.user_id),
            'note_username': note.user.username,
        }
    audit_log(type=AuditLogTypes.NOTE_SHARE_CREATED, user=instance.shared_by, related=instance, data=data)
