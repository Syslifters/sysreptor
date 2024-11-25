
import logging

from django.db.models import signals
from django.dispatch import receiver
from reportcreator_api.pentests.customfields.types import FieldDataType
from reportcreator_api.pentests.models.common import SourceEnum
from reportcreator_api.pentests.models.project import (
    PentestProject,
    ProjectType,
    ReportSection,
)

from .models import ProjectNumber

log = logging.getLogger(__name__)

@receiver(signals.post_save, sender=PentestProject)
def on_project_saved(sender, instance: PentestProject, created, **kwargs):
    """
    Signal handler for project save event.
    """ 
    p: ProjectType = instance.project_type
    if created and instance.source == SourceEnum.CREATED and not instance.copy_of_id and \
       'project_number' in p.all_report_fields_obj and \
       p.all_report_fields_obj["project_number"].type in [FieldDataType.STRING, FieldDataType.NUMBER] and \
       instance.data.get('project_number') in [None, p.all_report_fields_obj['project_number'].default]:
        counter, _ = ProjectNumber.objects.get_or_create(pk=1)
        counter.current_id += 1
        counter.save()
        for section in instance.sections.all():
            section: ReportSection
            if 'project_number' in section.section_fields:
                if section.field_definition['project_number'].type == FieldDataType.STRING:
                    report_data = {
                        'project_number': f"{counter.current_id}",
                    }
                    section.update_data(report_data)
                    section.save()
                elif section.field_definition['project_number'].type == FieldDataType.NUMBER:
                    report_data = {
                        'project_number': counter.current_id,
                    }
                    section.update_data(report_data)
                    section.save()



        

            