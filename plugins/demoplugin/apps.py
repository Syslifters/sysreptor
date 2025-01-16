import logging

from reportcreator_api.conf.plugins import PluginConfig

log = logging.getLogger(__name__)


class DemoPluginConfig(PluginConfig):
    plugin_id = 'db365aa0-ed36-4e90-93b6-a28effc4ed47'

    def ready(self) -> None:
        # Perform plugin initialization
        # e.g. register signal handlers, do some monkey patching, etc.
        log.info('Loading DemoPlugin...')

        from . import signals  # noqa
