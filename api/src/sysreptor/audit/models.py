import enum

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from sysreptor.utils.crypto.fields import EncryptedField
from sysreptor.utils.models import BaseModel


class AuditLogTypes(enum.StrEnum):
    LOGIN_SUCCESS = 'login_success'
    LOGOUT = 'logout'
    ADMIN_ENABLED = 'admin_enabled'
    ADMIN_DISABLED = 'admin_disabled'
    USER_CREATED = 'user_created'
    USER_UPDATED = 'user_updated'
    USER_DELETED = 'user_deleted'
    USER_PERMISSIONS_UPDATED = 'user_permissions_updated'
    PASSWORD_CHANGED = 'password_changed'  # noqa: S105
    MFA_CREATED = 'mfa_created'
    MFA_DELETED = 'mfa_deleted'
    AUTH_IDENTITY_CREATED = 'auth_identity_created'
    AUTH_IDENTITY_DELETED = 'auth_identity_deleted'
    API_TOKEN_CREATED = 'api_token_created'  # noqa: S105
    PROJECT_MEMBER_ADDED = 'project_member_added'
    PROJECT_MEMBER_REMOVED = 'project_member_removed'
    SETTINGS_CHANGED = 'settings_changed'
    BACKUP_STARTED = 'backup_started'
    RESTORE = 'restore'
    NOTE_SHARE_CREATED = 'note_share_created'


class AuditLogEntry(BaseModel):
    type = models.CharField(max_length=64, db_index=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.DO_NOTHING, db_constraint=False, related_name='+')
    data = EncryptedField(base_field=models.JSONField(default=dict, blank=True, encoder=DjangoJSONEncoder))

    content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.SET_NULL)
    object_id = models.UUIDField(null=True, blank=True)
    related = GenericForeignKey('content_type', 'object_id')

    class Meta(BaseModel.Meta):
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]
