from django.db import models

from sysreptor.pentests.models.project import PentestProject


class ChatThreadQuerySet(models.QuerySet):
    def only_permitted(self, user):
        if not user or user.is_anonymous or user.is_system_user:
            return self.none()

        return self \
            .filter(user=user) \
            .filter(models.Q(project__isnull=True) | models.Q(project__in=PentestProject.objects.only_permitted(user)))

    def annotate_has_checkpoints(self):
        from sysreptor.ai.models import LangchainCheckpoint

        return self.annotate(
            has_checkpoints=models.Exists(
                LangchainCheckpoint.objects.filter(thread=models.OuterRef('pk')),
            ),
        )

    def filter_has_checkpoints(self):
        return self \
            .annotate_has_checkpoints() \
            .filter(has_checkpoints=True)


class ChatThreadManager(models.Manager.from_queryset(ChatThreadQuerySet)):
    pass
