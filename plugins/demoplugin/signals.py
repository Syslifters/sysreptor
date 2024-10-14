
import logging

from django.db.models import signals
from django.dispatch import receiver
from reportcreator_api.pentests.models.project import PentestProject

log = logging.getLogger(__name__)

# Register django signal handlers
# https://docs.djangoproject.com/en/5.1/topics/signals/


@receiver(signals.post_save, sender=PentestProject)
def on_project_saved(sender, instance, created, **kwargs):
    """
    Signal handler for project save event.
    """
    if not created and 'name' in instance.changed_fields:
        old_name, new_name = instance.get_field_diff('name')
        log.info(f'Someone renamed project "{old_name}" to "{new_name}"')

