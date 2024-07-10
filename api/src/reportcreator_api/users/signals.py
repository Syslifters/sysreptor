from django.db.models import signals
from django.dispatch import receiver

from reportcreator_api.users.models import APIToken, PentestUser
from reportcreator_api.utils import license


@receiver(signals.pre_save, sender=PentestUser)
def user_count_license_check(sender, instance, *args, **kwargs):
    if not instance.is_active:
        return

    if instance.is_system_user and license.is_professional():
        return

    # User created
    created = instance.id is None or instance._state.adding
    if created:
        if license.is_professional():
            current_user_count = PentestUser.objects.get_licensed_user_count()
        else:
            current_user_count = PentestUser.objects.get_total_user_count()

        max_users = license.check_license().get('users', 1)
        if current_user_count + 1 > max_users:
            raise license.LicenseLimitExceededError(
                f'License limit exceeded. Your license allows max. {max_users} users. '
                'Please deactivate some users or extend your license.')

    # User updated
    if (created or 'is_superuser' in instance.changed_fields) and not instance.is_superuser and not license.is_professional():
        raise license.LicenseError('Cannot create non-superusers in Community edition. Professional license is required for user roles.')
    if (created or 'is_system_user' in instance.changed_fields) and instance.is_system_user and not license.is_professional():
        raise license.LicenseError('System users are not supported in Community edition. Professional license is required.')
    if not created and \
        ((instance.get_field_diff('is_superuser') == (False, True) and not license.is_professional()) or \
         (instance.get_field_diff('is_active') == (False, True))):
        if license.is_professional():
            current_user_count = PentestUser.objects.get_licensed_user_count()
        else:
            current_user_count = PentestUser.objects.get_total_user_count()
        max_users = license.check_license().get('users', 1)
        if current_user_count + 1 > max_users:
            raise license.LicenseError(f'License limit exceeded. Your license allows max. {max_users} users. Please deactivate some users or extend your license.')


@receiver(signals.pre_save, sender=APIToken)
def api_token_license_limit(sender, instance, *args, **kwargs):
    if license.is_professional() or not instance._state.adding:
        return

    current_apitoken_count = APIToken.objects \
        .filter(user=instance.user) \
        .only_active() \
        .count()
    if current_apitoken_count >= 1:
        raise license.LicenseLimitExceededError(
            'Community Edition allows max. 1 active API token per user. '
            'Please delete some tokens or upgrade to Professional.')

    if instance.expire_date:
        raise license.LicenseError('API token expiration is not supported in Community edition.')
