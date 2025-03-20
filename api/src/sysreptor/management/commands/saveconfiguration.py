import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from sysreptor.utils.configuration import configuration


class Command(BaseCommand):
    help = 'Save current configured settings from environment variables to the database settings.'

    def add_arguments(self, parser):
        parser.add_argument('--only-from-env', action='store_true', help='Only save configurations from environment variables')
        parser.add_argument('--skip-default', action='store_true', help='Skip saving default values')

    def handle(self, only_from_env=False, skip_default=False, **options):
        if not settings.LOAD_CONFIGURATIONS_FROM_ENV:
            logging.warning('LOAD_CONFIGURATIONS_FROM_ENV=False. Configurations are not loaded from environment variables.')
        if not settings.LOAD_CONFIGURATIONS_FROM_DB:
            logging.warning('LOAD_CONFIGURATIONS_FROM_DB=False. Saved configurations will not be loaded from the database.')

        configurations_to_update = {}
        for f in configuration.definition.fields:
            if only_from_env and not f.extra_info.get('set_in_env'):
                continue
            value = configuration.get(f.id)
            if skip_default and hasattr(f, 'default') and value == f.default:
                continue
            configurations_to_update[f.id] = value

        configuration.update(configurations_to_update, only_changed=False)
