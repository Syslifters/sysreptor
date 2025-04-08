from django.dispatch import receiver

from sysreptor import signals as sysreptor_signals
from sysreptor.notifications.models import RemoteNotificationSpec
from sysreptor.users.models import PentestUser
from sysreptor.utils.models import disable_for_loaddata


@receiver(sysreptor_signals.post_create, sender=RemoteNotificationSpec)
@disable_for_loaddata
def remotenotificationspec_created(sender, instance, *args, **kwargs):
    RemoteNotificationSpec.objects.assign_to_users(instance)


@receiver(sysreptor_signals.post_create, sender=PentestUser)
@disable_for_loaddata
def user_created(sender, instance, *args, **kwargs):
    RemoteNotificationSpec.objects.assign_to_notifications(instance)

