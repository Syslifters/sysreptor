from django.db.models import signals
from django.dispatch import receiver

from reportcreator_api.notifications.models import NotificationSpec
from reportcreator_api.users.models import PentestUser


@receiver(signals.post_save, sender=NotificationSpec)
def notification_created(sender, instance, created, *args, **kwargs):
    if not created:
        return
    
    NotificationSpec.objects.assign_to_users(instance)


@receiver(signals.post_save, sender=PentestUser)
def user_created(sender, instance, created, *args, **kwargs):
    if not created:
        return
    
    NotificationSpec.objects.assign_to_notifications(instance)

