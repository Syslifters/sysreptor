from django.db import models


class ChatThreadQuerySet(models.QuerySet):
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
