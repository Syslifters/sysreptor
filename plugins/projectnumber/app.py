from decouple import config
from reportcreator_api.conf.plugins import PluginConfig


class ProjectNumberPluginConfig(PluginConfig):
    plugin_id = '0003bc72-609c-49b6-9b01-3d7edd330353'
    settings = {
        'PLUGIN_PROJECTNUMBER_TEMPLATE': '',
        'PLUGIN_PROJECTNUMBER_FIELD_ID': ''
    }

    def ready(self) -> None:
        self.settings = self.load_settings()
        
        from . import signals  # noqa
    
    def load_settings(self):
        # If no TEMPLATE value is specified in app.env it will use this default template
        template = config('PLUGIN_PROJECTNUMBER_TEMPLATE', default='{{project_number}}')
        field_id = config('PLUGIN_PROJECTNUMBER_FIELD_ID', default='project_number')
        return {
            'PLUGIN_PROJECTNUMBER_TEMPLATE': template,
            'PLUGIN_PROJECTNUMBER_FIELD_ID': field_id
        }
