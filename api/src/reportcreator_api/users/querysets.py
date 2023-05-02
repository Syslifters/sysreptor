import pyotp
from fido2.server import Fido2Server, AttestedCredentialData
from fido2.webauthn import PublicKeyCredentialRpEntity, PublicKeyCredentialUserEntity, UserVerificationRequirement, AuthenticatorAttachment, \
    AttestationObject, CollectedClientData
from fido2.utils import websafe_encode, websafe_decode
from django.conf import settings
from django.db import models
from django.contrib.sessions.base_session import BaseSessionManager
from django.contrib.auth.models import UserManager
from django.utils.crypto import get_random_string


class SessionQueryset(models.QuerySet):
    def filter(self, **kwargs):
        from reportcreator_api.users.models import Session
        if 'session_key' in kwargs:
            kwargs['session_key_hash'] = Session.hash_session_key(kwargs['session_key'])
            del kwargs['session_key']
        return super().filter(**kwargs)


class SessionManager(BaseSessionManager, models.Manager.from_queryset(SessionQueryset)):
    use_in_migrations = True

    def save(self, session_key, session_dict, expire_date):
        from reportcreator_api.users.models import Session

        s = Session(
            session_key=session_key, 
            session_data=self.encode(session_dict), 
            expire_date=expire_date
        )
        if session_dict:
            s.save()
        else:
            s.delete()  # Clear sessions with no data.
        return s


class PentestUserQuerySet(models.QuerySet):
    def only_active(self):
        return self.filter(is_active=True)

    def only_permitted(self, user):
        from reportcreator_api.users.models import PentestUser
        if user.is_guest:
            # Only show users that are members in projects where the guest user is also a member
            return self \
                .filter(
                    models.Q(pk=user.pk) | 
                    models.Q(pk__in=PentestUser.objects.filter(projectmemberinfo__project__members__user=user)))
        else:
            return self

    def annotate_mfa_enabled(self):
        from reportcreator_api.users.models import MFAMethod
        return self \
            .annotate(is_mfa_enabled=models.Exists(MFAMethod.objects.filter(user=models.OuterRef('pk'))))
    
    def annotate_has_public_keys(self):
        from reportcreator_api.pentests.models import UserPublicKey
        return self \
            .annotate(has_public_keys=models.Exists(UserPublicKey.objects.only_enabled().filter(user=models.OuterRef('pk'))))
    
    def only_with_public_keys(self):
        return self \
            .annotate_has_public_keys() \
            .filter(has_public_keys=True)

    def get_licensed_user_count(self):
        return self \
            .only_active() \
            .exclude(is_system_user=True) \
            .count()

class PentestUserManager(UserManager, models.Manager.from_queryset(PentestUserQuerySet)):
    pass


class MFAMethodQuerySet(models.QuerySet):
    def only_permitted(self, user):
        if user.is_admin or user.is_user_manager:
            return self
        return self.filter(user=user)

    def default_order(self):
        from reportcreator_api.users.models import MFAMethodType
        return self \
            .annotate(method_type_order=models.Case(
                models.When(models.Q(method_type=MFAMethodType.FIDO2), then=1),
                models.When(models.Q(method_type=MFAMethodType.TOTP), then=2),
                models.When(models.Q(method_type=MFAMethodType.BACKUP), then=3),
                default=4
            )) \
            .order_by('-is_primary', 'method_type_order', 'created')


class MFAMethodManager(models.Manager.from_queryset(MFAMethodQuerySet)):
    def create_backup(self, save=True, **kwargs):
        from reportcreator_api.users.models import MFAMethod, MFAMethodType
        kwargs |= {
            'method_type': MFAMethodType.BACKUP,
            'data': {
                'backup_codes': [
                    get_random_string(length=12) for _ in range(10)
                ]
            }
        }
        out = MFAMethod(**kwargs)
        if save:
            out.save()
        return out

    def create_totp(self, save=True, **kwargs):
        from reportcreator_api.users.models import MFAMethod, MFAMethodType
        totp = pyotp.TOTP(pyotp.random_base32())
        kwargs |= {
            'method_type': MFAMethodType.TOTP,
            'data': {
                's': totp.secret,
                'digits': totp.digits,
                'interval': totp.interval,
            }
        }
        out = MFAMethod(**kwargs)
        if save:
            out.save()
        return out

    def get_fido2_user_credentials(self, user):
        from reportcreator_api.users.models import MFAMethodType
        fido2_methods = self.filter(user=user) \
            .filter(method_type=MFAMethodType.FIDO2)
        return [AttestedCredentialData(websafe_decode(m.data['device'])) for m in fido2_methods]

    def create_fido2_begin(self, user, **kwargs):
        from reportcreator_api.users.models import MFAMethod, MFAMethodType
        server = MFAMethod.get_fido2_server()
        options, state = server.register_begin(
            user=PublicKeyCredentialUserEntity(
                id=str(user.id).encode(),
                name=user.username,
                display_name=user.username,
            ),
            credentials=self.get_fido2_user_credentials(user),
            user_verification=UserVerificationRequirement.PREFERRED,
            authenticator_attachment=AuthenticatorAttachment.CROSS_PLATFORM
        )

        kwargs |= {
            'method_type': MFAMethodType.FIDO2,
            'data': {
                'options': dict(options),
                'state': state,
            },
        }
        return MFAMethod(**kwargs)

    def create_fido2_complete(self, instance, response, save=True):
        from reportcreator_api.users.models import MFAMethod
        server = MFAMethod.get_fido2_server()
        auth_data = server.register_complete(
            state=instance.data.get('state'), 
            response=response
        )
        instance.data = {
            'device': websafe_encode(auth_data.credential_data)
        }
        if save:
            instance.save()
        return instance

