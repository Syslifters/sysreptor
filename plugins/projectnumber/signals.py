
import logging

from django.db.models import F
from django.dispatch import receiver
from sysreptor.pentests.models import (
    PentestProject,
    ProjectType,
    ReportSection,
    SourceEnum,
)
from sysreptor.plugins import FieldDataType, configuration
from sysreptor.plugins import signals as sysreptor_signals

from .models import ProjectNumber
from .utils import format_project_number

log = logging.getLogger(__name__)


@receiver(sysreptor_signals.post_create, sender=PentestProject)
def on_project_saved(sender, instance: PentestProject, *args, **kwargs):
    """
    Signal handler for project save event.
    """
    p: ProjectType = instance.project_type
    field_id = configuration.PLUGIN_PROJECTNUMBER_FIELD_ID or 'project_number'
    if instance.source == SourceEnum.CREATED and not instance.copy_of_id and \
       field_id in p.all_report_fields_obj and \
       p.all_report_fields_obj[field_id].type == FieldDataType.STRING and \
       instance.data.get(field_id) in [None, p.all_report_fields_obj[field_id].default]:

        # Increment counter
        counter, _ = ProjectNumber.objects.update_or_create(
            pk=1,
            defaults={'current_id': F('current_id') + 1},
            create_defaults={'current_id': 1})

        # Fromat project number using the configured template from plugin settings
        projectnumber_str = format_project_number(
            template=configuration.PLUGIN_PROJECTNUMBER_TEMPLATE or '{{project_number}}',
            project_number=counter.current_id,
        )

        # Add tag
        instance.tags += [projectnumber_str]
        instance.save()

        # Search through sections to find the correct one
        for section in instance.sections.all():
            section: ReportSection
            if field_id in section.section_fields and section.field_definition[field_id].type == FieldDataType.STRING:
                section.update_data({ field_id: projectnumber_str })
                section.save()
