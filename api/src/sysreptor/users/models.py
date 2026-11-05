import functools
import hmac
import secrets
from base64 import b64encode
from collections.abc import Iterable
from io import BytesIO
from urllib.parse import urlparse

import pyotp
import qrcode
import qrcode.image.pil
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.contrib.sessions.base_session import AbstractBaseSession
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from fido2.server import Fido2Server, _verify_origin_for_rp
from fido2.webauthn import PublicKeyCredentialRpEntity

from sysreptor.users import querysets
from sysreptor.users.roles import Permission, expand_permissions, get_role_permissions
from sysreptor.utils.crypto.fields import EncryptedField
from sysreptor.utils.models import BaseModel
from sysreptor.utils.utils import get_random_color


class PentestUser(BaseModel, AbstractUser):
    password = EncryptedField(base_field=models.CharField(_("password"), max_length=128))
    must_change_password = models.BooleanField(_('Must change password at next login'), default=False)

    middle_name = models.CharField(_('Middle name'), max_length=255, null=True, blank=True)
    title_before = models.CharField(_('Title (before)'), max_length=255, null=True, blank=True)
    title_after = models.CharField(_('Title (after)'), max_length=255, null=True, blank=True)

    email = models.EmailField(_("Email address"), unique=True, null=True, blank=True)
    phone = models.CharField(_('Phone number'), max_length=255, null=True, blank=True)
    mobile = models.CharField(_('Phone number (mobile)'), max_length=255, null=True, blank=True)

    color = models.CharField(max_length=7, default=get_random_color, validators=[RegexValidator(r'^#[0-9a-fA-F]{6}$')])

    is_system_user = models.BooleanField(default=False, db_index=True)
    roles = ArrayField(base_field=models.CharField(max_length=255), default=list, blank=True, db_index=True)

    can_login_local = models.BooleanField(default=True)
    failed_mfa_attempts = models.PositiveIntegerField(default=0)

    REQUIRED_FIELDS = []

    objects = querysets.PentestUserManager()

    class Meta(BaseModel.Meta, AbstractUser.Meta):
        pass

    @property
    def name(self) -> str:
        return ((self.title_before + ' ') if self.title_before else '') + \
            ((self.first_name + ' ') if self.first_name else '') + \
            ((self.middle_name + ' ') if self.middle_name else '') + \
            (self.last_name or '') + \
            ((', ' + self.title_after) if self.title_after else '')

    def restrict_permissions(self, permissions: Iterable[Permission]) -> None:
        """
        In-memory allowlist that can only reduce effective permissions (not persisted).
        Intersected with role permissions in effective_permissions. Ignored when is_admin.
        """
        self._permissions_restriction = expand_permissions(permissions)

    @property
    def effective_permissions(self) -> list[str]:
        if not self.is_active or self.is_system_user:
            return []
        elif self.is_admin:
            return list(p.value for p in Permission)
        perms = get_role_permissions(self.roles)
        if restriction := getattr(self, '_permissions_restriction', None):
            perms &= restriction
        return list(p.value for p in perms)

    def has_permission(self, permission: str) -> bool:
        if not self.is_active or self.is_system_user:
            return False
        elif self.is_admin:
            return True
        return permission in self.effective_permissions

    @property
    def has_password(self) -> bool:
        return self.password and self.has_usable_password()

    @functools.cached_property
    def can_login_sso(self) -> bool:
        return bool(self.auth_identities.all())

    @property
    def is_admin(self) -> bool:
        return self.is_active and self.is_superuser and getattr(self, 'admin_permissions_enabled', False)

    @functools.cached_property
    def referenced_filenames(self) -> set:
        names = set()
        for note in self.notes.all():
            names |= note.referenced_filenames
        return names

    def is_file_referenced(self, f) -> bool:
        return f.name in self.referenced_filenames

    def save(self, *args, **kwargs):
        # Convert empty string to None
        self.email = self.email or None
        return super().save(*args, **kwargs)


class AuthIdentity(BaseModel):
    PROVIDER_REMOTE_USER = 'remoteuser'

    user = models.ForeignKey(to=PentestUser, on_delete=models.CASCADE, related_name='auth_identities')
    provider = models.CharField(max_length=255)
    identifier = models.CharField(max_length=255)

    class Meta(BaseModel.Meta):
        unique_together = ['provider', 'identifier']


class APIToken(BaseModel):
    TOKEN_PREFIX = 'sysreptor_'  # noqa: S105

    user = models.ForeignKey(to=PentestUser, on_delete=models.CASCADE, related_name='api_tokens')
    token_hash = models.CharField(max_length=256)
    name = models.CharField(max_length=255, default='API Token')
    expire_date = models.DateField(null=True, blank=True)
    last_used = models.DateTimeField(null=True, blank=True, editable=False)
    admin_permissions_enabled = models.BooleanField(default=False)
    is_project_restricted = models.BooleanField(default=False, editable=False)
    projects = models.ManyToManyField('pentests.PentestProject', related_name='api_tokens', blank=True)
    read_only = models.BooleanField(default=False)
    token_plaintext = None

    objects = querysets.APITokenManager()

    class Meta(BaseModel.Meta):
        constraints = [
            models.CheckConstraint(
                condition=models.Q(is_project_restricted=False) | models.Q(admin_permissions_enabled=False),
                name='apitoken_project_no_admin',
            ),
            models.CheckConstraint(
                condition=models.Q(read_only=False) | models.Q(is_project_restricted=True),
                name='apitoken_read_only_project',
            ),
        ]

    def save(self, *args, **kwargs):
        from sysreptor.users.auth import UnsaltedSHA3_256PasswordHasher
        if not self.token_hash:
            self.token_plaintext = secrets.token_bytes(32).hex()
            self.token_hash = UnsaltedSHA3_256PasswordHasher().encode(self.token_plaintext, '')
        return super().save(*args, **kwargs)

    @property
    def token_formatted(self) -> str:
        if not self.token_plaintext:
            return None
        return self.TOKEN_PREFIX + b64encode(f'{self.id}:{self.token_plaintext}'.encode()).decode()

    def validate_token(self, token_plaintext):
        from sysreptor.users.auth import UnsaltedSHA3_256PasswordHasher
        return UnsaltedSHA3_256PasswordHasher().verify(token_plaintext, self.token_hash)



class Session(BaseModel, AbstractBaseSession):
    session_key = EncryptedField(base_field=models.CharField(_("session key"), max_length=40))
    session_data = EncryptedField(base_field=models.TextField(_("session data")))

    session_key_hash = models.BinaryField(max_length=32, unique=True)
    user = models.ForeignKey(to=PentestUser, on_delete=models.CASCADE, null=True, blank=True, related_name='sessions')

    objects = querysets.SessionManager()

    class Meta(BaseModel.Meta, AbstractBaseSession.Meta):
        pass

    def __str__(self) -> str:
        return f'Session {self.id}'

    def save(self, *args, **kwargs) -> None:
        self.session_key_hash = self.hash_session_key(self.session_key)
        return super().save(*args, **kwargs)

    @classmethod
    def get_session_store_class(cls):
        from sysreptor.users.backends.session import SessionStore
        return SessionStore

    @classmethod
    def hash_session_key(cls, session_key) -> bytes:
        return hmac.new(key=settings.SECRET_KEY.encode(), msg=session_key.encode(), digestmod='sha3_256').digest()


class MFAMethodType(models.TextChoices):
    TOTP = 'totp', _('TOTP')
    FIDO2 = 'fido2', _('FIDO2')
    BACKUP = 'backup', _('Backup codes')


class MFAMethod(BaseModel):
    user = models.ForeignKey(to=PentestUser, on_delete=models.CASCADE, related_name='mfa_methods')
    method_type = models.CharField(max_length=255, choices=MFAMethodType.choices)
    is_primary = models.BooleanField(default=False)
    name = models.CharField(max_length=255, default="", blank=True)
    data = EncryptedField(base_field=models.JSONField())

    objects = querysets.MFAMethodManager()

    def get_totp_qrcode(self):
        if self.method_type != MFAMethodType.TOTP:
            return None

        totp = pyotp.TOTP(name=self.user.username, issuer=settings.MFA_SERVER_NAME, **self.data)
        img = qrcode.make(totp.provisioning_uri(), image_factory=qrcode.image.pil.PilImage)
        buf = BytesIO()
        img.save(buf, format='PNG')
        img.close()
        return 'data:image/png;base64,' + b64encode(buf.getvalue()).decode()

    def verify_code(self, code):
        if self.method_type == MFAMethodType.BACKUP:
            if code in self.data.get('backup_codes', []):
                self.data['backup_codes'].remove(code)
                self.save()
                return True
            return False
        elif self.method_type == MFAMethodType.TOTP:
            totp = pyotp.TOTP(**self.data)
            return totp.verify(code, valid_window=1)
        return False

    @classmethod
    def get_fido2_server(cls):
        rp_id = settings.MFA_FIDO2_RP_ID

        def verify_origin(origin):
            if not settings.MFA_FIDO2_RP_ID:
                raise ValueError('The setting MFA_FIDO2_RP_ID is not configured. Set it to your hostname that you use to access your installation e.g. "sysreptor.example.com"')

            # Do not require HTTPS for localhost
            url = urlparse(origin)
            if rp_id == 'localhost':
                return url.hostname == rp_id
            return _verify_origin_for_rp(rp_id)(origin)

        return Fido2Server(
            rp=PublicKeyCredentialRpEntity(id=rp_id, name=settings.MFA_SERVER_NAME),
            verify_origin=verify_origin,
        )
