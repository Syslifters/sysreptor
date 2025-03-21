
import logging

from django.dispatch import receiver
from sysreptor.pentests.models import PentestProject
from sysreptor import signals as sysreptor_signals

log = logging.getLogger(__name__)

# Register django signal handlers
# https://docs.djangoproject.com/en/stable/topics/signals/

@receiver(sysreptor_signals.post_update, sender=PentestProject)
def on_project_updated(sender, instance, changed_fields, *args, **kwargs):
    """
    Signal handler for project save event.
    """
    if 'name' in changed_fields:
        old_name, new_name = instance.get_field_diff('name')
        log.info(f'Someone renamed project "{old_name}" to "{new_name}"')

