
import logging

from django.dispatch import receiver
from reportcreator_api import signals as sysreptor_signals
from reportcreator_api.pentests.models.project import PentestProject

log = logging.getLogger(__name__)

# Register django signal handlers
# https://docs.djangoproject.com/en/5.1/topics/signals/


@receiver(sysreptor_signals.post_update, sender=PentestProject)
def on_project_saved(sender, instance, changed_fields, *args, **kwargs):
    """
    Signal handler for project save event.
    """
    if 'name' in changed_fields:
        old_name, new_name = instance.get_field_diff('name')
        log.info(f'Someone renamed project "{old_name}" to "{new_name}"')

