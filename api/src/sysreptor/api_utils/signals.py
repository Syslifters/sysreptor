import logging

from django.apps import apps
from django.conf import settings
from django.db.models.signals import post_migrate
from django.dispatch import receiver

from sysreptor.utils.configuration import configuration
from sysreptor.utils.crypto import EncryptionKey


@receiver(post_migrate, sender=apps.get_app_config('api_utils'))
def check_configuration(sender, **kwargs):
    """
    Validate configuration on startup without using Django's system check framework.

    Django system checks run for management commands like ``migrate`` *before* the command
    logic executes. At that point, database-backed configuration can't be reliably read:
    the database connection might not be available yet and (more importantly) the tables
    required for reading configuration may not exist until migrations are applied.
    """

    # Validate settings from environment variables
    for msg in EncryptionKey.check_config(settings):
        logging.warning(msg)

    # Validate DB-stored configuration
    try:
        for oidc_config in configuration.OIDC_AUTHLIB_OAUTH_CLIENTS.values():
            if oidc_config.get('require_email_verified') is None:
                logging.warning('OIDC_AUTHLIB_OAUTH_CLIENTS: require_email_verified is not set. Defaulting to accepting unverified emails.')
    except Exception:
        # Ignore errors
        return
