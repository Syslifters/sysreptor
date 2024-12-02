
import logging

from django.apps import apps
from django.db.models import signals
from django.dispatch import receiver
from django.template import Context, Engine
from reportcreator_api.pentests.customfields.types import FieldDataType
from reportcreator_api.pentests.models.common import SourceEnum
from reportcreator_api.pentests.models.project import (
    PentestProject,
    ProjectType,
    ReportSection,
)

from .app import ProjectNumberPluginConfig
from .models import ProjectNumber

log = logging.getLogger(__name__)

custom_engine = Engine(
    builtins=['sysreptor_plugins.projectnumber.templatetags.random_number'], 
)

class Default(dict):
    def __missing__(self, key): 
        return key.join("{}")
    
@receiver(signals.post_save, sender=PentestProject)
def on_project_saved(sender, instance: PentestProject, created, **kwargs):
    """
    Signal handler for project save event.
    """ 
    p: ProjectType = instance.project_type
    field_id = apps.get_app_config(ProjectNumberPluginConfig.label).settings.get('PLUGIN_PROJECTNUMBER_FIELD_ID', '')
    if created and instance.source == SourceEnum.CREATED and not instance.copy_of_id and \
       field_id in p.all_report_fields_obj and \
       p.all_report_fields_obj[field_id].type == FieldDataType.STRING and \
       instance.data.get(field_id) in [None, p.all_report_fields_obj[field_id].default]:
        
        # Get counter and update it
        counter, _ = ProjectNumber.objects.get_or_create(pk=1)
        counter.current_id += 1
        counter.save()
        
        settings = apps.get_app_config(ProjectNumberPluginConfig.label).settings.get('PLUGIN_PROJECTNUMBER_TEMPLATE', '')
        template = custom_engine.from_string(settings)
        context = Context({
            'project_number': counter.current_id,
        })
        
        # Add tag
        instance.tags = [template.render(context)]
        instance.save()
        
        # Search through sections to find the correct one
        for section in instance.sections.all():
            section: ReportSection
            if field_id in section.section_fields:
                if section.field_definition[field_id].type == FieldDataType.STRING:
                    # Get template and render value into found field. 
                    report_data = {
                        field_id: template.render(context),
                    }
                    section.update_data(report_data)
                    section.save()
