from decouple import config
from reportcreator_api.conf.plugins import PluginConfig
from reportcreator_api.pentests.customfields.types import FieldDefinition, StringField

from .utils import validate_template


class ProjectNumberPluginConfig(PluginConfig):
    """
    This pluign adds sequential project numbers to newly created projects. 
    The project number formatting can be customized using Django Templates.
    """

    plugin_id = '0003bc72-609c-49b6-9b01-3d7edd330353'

    configuration_definition = FieldDefinition(fields=[
        StringField(
            id='PLUGIN_PROJECTNUMBER_TEMPLATE', 
            default='{{project_number}}',
            extra_info={'validate': validate_template},
            help_text='Django Template string to format the project number e.g. pad with leading zeros, add current year, etc. See the plugin\'s README.md on GitHub for examples.'),
        StringField(
            id='PLUGIN_PROJECTNUMBER_FIELD_ID', 
            default='project_number', 
            pattern=r'^[a-zA-Z_][a-zA-Z0-9_]*$',
            help_text='The ID of the custom field to store the project number. This field must be present in designs and has type "string".'),
    ])

    # TODO: refactor settings handling
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
