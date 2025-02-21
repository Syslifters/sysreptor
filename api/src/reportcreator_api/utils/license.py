import base64
import hashlib
import json
import logging
from pathlib import Path
from uuid import uuid4

from asgiref.sync import sync_to_async
from Cryptodome.Hash import SHA512
from Cryptodome.PublicKey import ECC
from Cryptodome.Signature import eddsa
from django.conf import settings
from django.db import models
from django.utils import dateparse, timezone
from rest_framework import permissions

from reportcreator_api.utils.configuration import configuration
from reportcreator_api.utils.decorators import cache

LICENSE_VALIDATION_KEYS = [
    {'id': 'amber', 'algorithm': 'ed25519', 'key': 'MCowBQYDK2VwAyEAkqCS3lZbrzh+2mKTYymqPHtKBrh8glFxnj9OcoQR9xQ='},
    {'id': 'silver', 'algorithm': 'ed25519', 'key': 'MCowBQYDK2VwAyEAwu/cl0CZSSBFOzFSz/hhUQQjHIKiT4RS3ekPevSKn7w='},
    {'id': 'magenta', 'algorithm': 'ed25519', 'key': 'MCowBQYDK2VwAyEAd10mgfTx0fuPO6KwcYU98RLhreCF+BQCeI6CAs0YztA='},
]


class LicenseError(Exception):
    def __init__(self, detail: str|dict) -> None:
        super().__init__(detail)
        self.detail = detail


class LicenseLimitExceededError(LicenseError):
    pass


class LicenseType(models.TextChoices):
    COMMUNITY = 'community', 'Community'
    PROFESSIONAL = 'professional', 'Professional'


class ProfessionalLicenseRequired(permissions.BasePermission):
    def has_permission(self, request, view):
        if not is_professional():
            raise LicenseError('Professional license required')
        return True


def verify_signature(data: str, signature: dict):
    public_key = next(filter(lambda k: k['id'] == signature['key_id'], LICENSE_VALIDATION_KEYS), None)
    if not public_key:
        return False
    if public_key['algorithm'] != signature['algorithm'] or signature['algorithm'] != 'ed25519':
        return False

    try:
        verifier = eddsa.new(key=ECC.import_key(base64.b64decode(public_key['key'])), mode='rfc8032')
        verifier.verify(msg_or_hash=SHA512.new(data.encode()), signature=base64.b64decode(signature['signature']))
        return True
    except Exception:
        return False


def parse_date(s):
    out = dateparse.parse_date(s)
    if out is None:
        raise ValueError()
    return out


def decode_license(license):
    try:
        license_wrapper = json.loads(base64.b64decode(license))
        for signature in license_wrapper['signatures']:
            if verify_signature(license_wrapper['data'], signature):
                license_data = json.loads(license_wrapper['data'])
                license_data['valid_from'] = parse_date(license_data['valid_from'])
                license_data['valid_until'] = parse_date(license_data['valid_until'])
                if not isinstance(license_data['users'], int) or license_data['users'] <= 0:
                    raise LicenseError(license_data | {'error': 'Invalid user count in license'})
                return license_data
        else:
            raise LicenseError('No valid signature found for license')
    except LicenseError:
        raise
    except Exception as ex:
        raise LicenseError('Failed to load license: Invalid format.') from ex


def decode_and_validate_license(license, skip_db_checks=False, skip_limit_validation=False):
    try:
        if not license:
            raise LicenseError(None)

        license_data = decode_license(license)
        if not skip_limit_validation:
            # Validate license
            period_info = f"The license is valid from {license_data['valid_from'].isoformat()} until {license_data['valid_until'].isoformat()}"
            if license_data['valid_from'] > timezone.now().date():
                raise LicenseError(license_data | {'error': 'License not yet valid: ' + period_info})
            elif license_data['valid_until'] < timezone.now().date():
                raise LicenseError(license_data | {'error': 'License expired: ' + period_info})

            # Validate license limits not exceeded
            if not skip_db_checks:
                from reportcreator_api.users.models import PentestUser
                current_user_count = PentestUser.objects.get_licensed_user_count()
                if current_user_count > license_data['users']:
                    raise LicenseError(license_data | {
                        'error': f"License limit exceeded: You licensed max. {license_data['users']} users, but have currently {current_user_count} active users. "
                                "Falling back to the free license. Please deactivate some users or extend your license.",
                    })

        # All license checks are valid
        return {
            'type': LicenseType.PROFESSIONAL,
            'error': None,
        } | license_data
    except LicenseError as ex:
        if license:
            logging.exception('License validation failed')

        error_details = ex.detail if isinstance(ex.detail, dict) else {'error': ex.detail}
        return error_details | {
            'type': LicenseType.COMMUNITY,
            'users': 3,
        }


def get_license_hash():
    if not settings.LICENSE:
        return None
    try:
        return 'sha3_256$$' + hashlib.sha3_256(base64.b64decode(settings.LICENSE)).hexdigest()
    except Exception:
        return None


@cache('license.license_info', timeout=10 * 60)
def check_license(**kwargs):
    return decode_and_validate_license(license=settings.LICENSE, **kwargs)


async def acheck_license(**kwargs):
    return await sync_to_async(check_license)(**kwargs)


def get_installation_id():
    value = configuration.INSTALLATION_ID

    if not value:
        # initialize from file
        installation_id_path: Path = settings.MEDIA_ROOT / 'installation_id'
        if installation_id_path.exists():
            value = installation_id_path.read_text().strip()
        if not value:
            value = str(uuid4())
        configuration.update({'INSTALLATION_ID': value})
        try:
            installation_id_path.unlink(missing_ok=True)
        except Exception:  # noqa: S110
            pass
    return value


def get_license_info():
    from reportcreator_api.conf import plugins
    from reportcreator_api.tasks.models import LicenseActivationInfo
    from reportcreator_api.users.models import PentestUser

    activation_info = LicenseActivationInfo.objects.current()
    return check_license() | {
        'license_hash': get_license_hash(),
        'active_users': PentestUser.objects.get_licensed_user_count(),
        'total_users': PentestUser.objects.get_total_user_count(),
        'installation_id': get_installation_id(),
        'software_version': settings.VERSION,
        'plugins': [p.name.split('.')[-1] for p in plugins.enabled_plugins],
        'activation_info': {
            'created': activation_info.created,
            'license_hash': activation_info.license_hash,
            'last_activation_time': activation_info.last_activation_time,
        },
    }

async def aget_license_info():
    return await sync_to_async(get_license_info)()


def is_professional(**kwargs):
    return check_license(**kwargs).get('type', LicenseType.COMMUNITY) == LicenseType.PROFESSIONAL


async def ais_professional(**kwargs):
    return (await acheck_license(**kwargs)).get('type', LicenseType.COMMUNITY) == LicenseType.PROFESSIONAL


def validate_login_allowed(user):
    if not is_professional() and not (user.is_superuser or user.is_system_user):
        raise LicenseError('Only superusers are allowed to login. A Professional license is required to enable user roles.')
    return True
