from django.dispatch import receiver

from reportcreator_api import signals as sysreptor_signals
from reportcreator_api.notifications.models import NotificationSpec
from reportcreator_api.users.models import PentestUser
from reportcreator_api.utils.models import disable_for_loaddata


@receiver(sysreptor_signals.post_create, sender=NotificationSpec)
@disable_for_loaddata
def notification_created(sender, instance, *args, **kwargs):
    NotificationSpec.objects.assign_to_users(instance)


@receiver(sysreptor_signals.post_create, sender=PentestUser)
@disable_for_loaddata
def user_created(sender, instance, *args, **kwargs):
    NotificationSpec.objects.assign_to_notifications(instance)

