
import base64
import json
import logging
from Cryptodome.Hash import SHA512
from Cryptodome.PublicKey import ECC
from Cryptodome.Signature import eddsa
from django.conf import settings
from django.db import models
from django.utils import dateparse, timezone
from rest_framework import permissions

from reportcreator_api.utils.decorators import cache


class LicenseError(Exception):
    def __init__(self, detail: str) -> None:
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
    public_key = next(filter(lambda k: k['id'] == signature['key_id'], settings.LICENSE_VALIDATION_KEYS), None)
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
                    raise LicenseError('Invalid user count in license')
                return license_data
        else:
            raise LicenseError('No valid signature found for license')
    except LicenseError:
        raise
    except Exception as ex:
        raise LicenseError('Failed to load license: Invalid format.') from ex


def decode_and_validate_license(license):
    from reportcreator_api.users.models import PentestUser

    try:
        if not license:
            raise LicenseError(None)
        
        # Validate license
        license_data = decode_license(license)
        period_info = f"The license is valid from {license_data['valid_from'].isoformat()} until {license_data['valid_until'].isoformat()}"
        if license_data['valid_from'] > timezone.now().date():
            raise LicenseError('License not yet valid: ' + period_info)
        elif license_data['valid_until'] < timezone.now().date():
            raise LicenseError('License expired: ' + period_info)
        
        # Validate license limits not exceeded
        current_user_count = PentestUser.objects.get_licensed_user_count()
        if current_user_count > license_data['users']:
            raise LicenseError(
                f"License limit exceeded: You licensed max. {license_data['users']} users, but have currently {current_user_count} active users. "
                "Falling back to the free license. Please deactivate some users or extend your license.")

        # All license checks are valid
        return {
            'type': LicenseType.PROFESSIONAL,
            'error': None,
        } | license_data
    except LicenseError as ex:
        if license:
            logging.exception('License validation failed')
        return {
            'type': LicenseType.COMMUNITY,
            'users': settings.LICENSE_COMMUNITY_MAX_USERS,
            'error': ex.detail,
        }


@cache('license.license_info', timeout=10 * 60)
def check_license():
    return decode_and_validate_license(settings.LICENSE)


def is_professional():
    return check_license().get('type', LicenseType.COMMUNITY) == LicenseType.PROFESSIONAL

