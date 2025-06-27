from sysreptor.plugins import PluginConfig


class ExcalidrawPluginConfig(PluginConfig):
    """
    Add Excalidraw to SysReptor projects.
    """

    plugin_id = 'c50b19ff-db68-4a83-9508-80ff6b6d2498'

    def ready(self):
        from . import signals  # noqa

