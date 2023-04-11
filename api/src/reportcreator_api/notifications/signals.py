from django.db.models import signals
from django.dispatch import receiver

from reportcreator_api.notifications.models import NotificationSpec
from reportcreator_api.users.models import PentestUser
from reportcreator_api.utils.models import disable_for_loaddata


@receiver(signals.post_save, sender=NotificationSpec)
@disable_for_loaddata
def notification_created(sender, instance, created, *args, **kwargs):
    if not created:
        return
    
    NotificationSpec.objects.assign_to_users(instance)


@receiver(signals.post_save, sender=PentestUser)
@disable_for_loaddata
def user_created(sender, instance, created, *args, **kwargs):
    if not created:
        return
    
    NotificationSpec.objects.assign_to_notifications(instance)

