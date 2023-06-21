import functools
import hmac
import pyotp
import qrcode
import qrcode.image.pil
from urllib.parse import urlparse
from io import BytesIO
from base64 import b64encode
from fido2.server import Fido2Server, _verify_origin_for_rp
from fido2.webauthn import PublicKeyCredentialRpEntity
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.sessions.base_session import AbstractBaseSession
from django.utils.translation import gettext_lazy as _

from reportcreator_api.utils import license
from reportcreator_api.archive.crypto.fields import EncryptedField
from reportcreator_api.utils.models import BaseModel
from reportcreator_api.users import querysets


class PentestUser(BaseModel, AbstractUser):
    password = EncryptedField(base_field=models.CharField(_("password"), max_length=128))

    middle_name = models.CharField(_('Middle name'), max_length=255, null=True, blank=True)
    title_before = models.CharField(_('Title (before)'), max_length=255, null=True, blank=True)
    title_after = models.CharField(_('Title (after)'), max_length=255, null=True, blank=True)

    email = models.EmailField(_("Email address"), null=True, blank=True)
    phone = models.CharField(_('Phone number'), max_length=255, null=True, blank=True)
    mobile = models.CharField(_('Phone number (mobile)'), max_length=255, null=True, blank=True)

    is_designer = models.BooleanField(default=False, db_index=True)
    is_template_editor = models.BooleanField(default=False, db_index=True)
    is_user_manager = models.BooleanField(default=False, db_index=True)
    is_guest = models.BooleanField(default=False, db_index=True)
    is_system_user = models.BooleanField(default=False, db_index=True)
    is_global_archiver = models.BooleanField(default=False, db_index=True)

    REQUIRED_FIELDS = []

    objects = querysets.PentestUserManager()

    @property
    def name(self):
        return ((self.title_before + ' ') if self.title_before else '') + \
            ((self.first_name + ' ') if self.first_name else '') + \
            ((self.middle_name + ' ') if self.middle_name else '') + \
            (self.last_name or '') + \
            ((', ' + self.title_after) if self.title_after else '') 

    @property
    def scope(self):
        return (['admin'] if self.is_admin else []) + \
               (['template_editor'] if self.is_template_editor or self.is_admin else []) + \
               (['designer'] if self.is_designer or self.is_admin else []) + \
               (['user_manager'] if self.is_user_manager or self.is_admin else []) + \
               (['guest'] if self.is_guest and not self.is_admin else []) + \
               (['system'] if self.is_system_user else [])

    @property
    def can_login_local(self):
        return settings.LOCAL_USER_AUTH_ENABLED and self.password and self.has_usable_password()

    @functools.cached_property
    def can_login_sso(self):
        return bool(self.auth_identities.all())
    
    @property
    def is_admin(self):
        return self.is_active and self.is_superuser and \
            getattr(self, 'admin_permissions_enabled', False) if license.is_professional() else True


class AuthIdentity(BaseModel):
    PROVIDER_REMOTE_USER = 'remoteuser'

    user = models.ForeignKey(to=PentestUser, on_delete=models.CASCADE, related_name='auth_identities')
    provider = models.CharField(max_length=255)
    identifier = models.CharField(max_length=255)

    class Meta(BaseModel.Meta):
        unique_together = ['provider', 'identifier']


class Session(AbstractBaseSession):
    session_key = EncryptedField(base_field=models.CharField(_("session key"), max_length=40))
    session_data = EncryptedField(base_field=models.TextField(_("session data")))

    session_key_hash = models.BinaryField(max_length=32, primary_key=True)

    objects = querysets.SessionManager()

    def save(self, *args, **kwargs) -> None:
        self.session_key_hash = self.hash_session_key(self.session_key)
        return super().save(*args, **kwargs)

    @classmethod
    def get_session_store_class(cls):
        from reportcreator_api.users.backends.session import SessionStore
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
