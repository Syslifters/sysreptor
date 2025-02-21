from reportcreator_api.conf.plugins import PluginConfig


class RenderFindingsPluginConfig(PluginConfig):
    """
    This plugin exports single findings to a PDF without rendering the whole report.
    You might need to update your design to propertly support and customize this plugin.
    """

    plugin_id = '62d0f5ae-5c07-47c6-9203-a9d9c3dbffb2'
    professional_only = True
