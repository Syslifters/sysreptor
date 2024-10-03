from reportcreator_api.conf.plugins import PluginConfig


class DemoPluginConfig(PluginConfig):
    plugin_id = 'db365aa0-ed36-4e90-93b6-a28effc4ed47'

    def ready(self) -> None:
        from . import signals  # noqa

