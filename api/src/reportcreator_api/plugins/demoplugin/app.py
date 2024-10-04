from reportcreator_api.conf.plugins import PluginConfig, PluginMenuEntry, PluginMenuId


class DemoPluginConfig(PluginConfig):
    plugin_id = 'db365aa0-ed36-4e90-93b6-a28effc4ed47'
    display_name = 'Demo Plugin'

    menu_entries = [
        PluginMenuEntry(
            id='demo',
            menu_id=PluginMenuId.MAIN,
            url=f'/static/plugins/{plugin_id}/index.html',
            name='DemoPlugin Main Menu Entry',
            icon='mdi-puzzle',
        ),
    ]

    def ready(self) -> None:
        from . import signals  # noqa

