from reportcreator_api.conf.plugins import PluginConfig, PluginMenuEntry, PluginMenuId


class DemoPluginConfig(PluginConfig):
    plugin_id = 'db365aa0-ed36-4e90-93b6-a28effc4ed47'

    menu_entries = [
        PluginMenuEntry(
            id='demo',
            menu_id=PluginMenuId.MAIN,
            url=f'/static/plugins/{plugin_id}/index.html',
            title='DemoPlugin Main Menu Entry',
            icon='mdi-puzzle',
        ),
        # TODO: per-project menu entry: get project ID, fetch project from API, print project data
    ]

    # TODO: use custom API endpoints and use them in frontend
    # TODO: modify CSP rules in ready() method ???

    def ready(self) -> None:
        from . import signals  # noqa

