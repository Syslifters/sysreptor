from sysreptor.plugins import PluginConfig


class ExcalidrawPluginConfig(PluginConfig):
    plugin_id = 'c50b19ff-db68-4a83-9508-80ff6b6d2498'

    def ready(self):
        from . import signals  # noqa

