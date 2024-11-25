import logging

from reportcreator_api.conf.plugins import PluginConfig

log = logging.getLogger(__name__)


class ProjectNumberPluginConfig(PluginConfig):
    plugin_id = '0003bc72-609c-49b6-9b01-3d7edd330353'

    def ready(self) -> None:
        # Perform plugin initialization
        # e.g. register signal handlers, do some monkey patching, etc.
        log.info('Loading Project Number Plugin...')

        from . import signals  # noqa
