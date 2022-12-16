from django.db import models
from django.contrib.auth.models import UserManager


class PentestUserQuerySet(models.QuerySet):
    def only_permitted(self, user):
        from reportcreator_api.users.models import PentestUser
        if user.is_guest:
            # Only show users that are members in projects where the guest user is also a member
            return self \
                .filter(
                    models.Q(pk=user.pk) | 
                    models.Q(pk__in=PentestUser.objects.filter(projectmemberinfo__project__members__user=user)))
        else:
            return self


class PentestUserManager(UserManager, models.Manager.from_queryset(PentestUserQuerySet)):
    pass

