"""
PostgreSQL checkpointer for LangGraph using Django ORM.
Stores conversation state and enables thread persistence.
"""
import json
from collections.abc import Iterator
from typing import Any

from asgiref.sync import sync_to_async
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Subquery
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    get_serializable_checkpoint_metadata,
)

from sysreptor.ai.models import LangchainCheckpoint
from sysreptor.utils.utils import copy_keys


class DjangoModelCheckpointer(BaseCheckpointSaver):
    def format_configurable(self, checkpoint: Checkpoint) -> dict[str, Any]:
        return {k: str(v) for k, v in copy_keys(checkpoint, ['thread_id', 'checkpoint_ns', 'checkpoint_id']).items()}

    def format_checkpoint_tuple(self, checkpoint: LangchainCheckpoint) -> CheckpointTuple:
        return CheckpointTuple(
            config={
                'configurable': self.format_configurable(checkpoint=checkpoint),
            },
            checkpoint=self.serde.loads_typed((checkpoint.checkpoint_type, checkpoint.checkpoint)),
            metadata=json.loads(checkpoint.metadata or {}),
            parent_config={
                "configurable": self.format_configurable(checkpoint=checkpoint) | {
                    "checkpoint_id": str(checkpoint.parent_checkpoint_id),
                },
            } if checkpoint.parent_checkpoint_id else None,
            pending_writes=self.serde.loads_typed((checkpoint.pending_writes_type, checkpoint.pending_writes)) if checkpoint.pending_writes else [],
        )

    def get_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        checkpoint = LangchainCheckpoint.objects \
            .filter(**self.format_configurable(config['configurable'])) \
            .order_by("-created") \
            .first()
        if not checkpoint:
            return None
        return self.format_checkpoint_tuple(checkpoint=checkpoint)

    def list(self, config: RunnableConfig, *, filter: dict[str, Any] | None = None, before: RunnableConfig | None = None, limit: int | None = None) -> Iterator[CheckpointTuple]:
        filters = copy_keys(config['configurable'], ['thread_id', 'checkpoint_ns'])
        qs = LangchainCheckpoint.objects \
            .filter(**filters) \
            .order_by("-created")
        if before and before["configurable"].get("checkpoint_id"):
            qs = qs.filter(created__lt=Subquery(
                LangchainCheckpoint.objects
                    .filter(**filters)
                    .filter(checkpoint_id=before["configurable"]["checkpoint_id"])
                    .values("created"),
                ))
        if limit:
            qs = qs[:limit]

        return [self.format_checkpoint_tuple(checkpoint=checkpoint) for checkpoint in qs]

    def put(self, config: dict, checkpoint: Checkpoint, metadata: CheckpointMetadata, new_versions: dict) -> RunnableConfig:
        t, d = self.serde.dumps_typed(checkpoint)
        defaults = {
            'checkpoint_type': t,
            'checkpoint': d,
            'metadata': json.dumps(get_serializable_checkpoint_metadata(config=config, metadata=metadata), cls=DjangoJSONEncoder).encode(),
        }
        instance, _ = LangchainCheckpoint.objects.update_or_create(
            **self.format_configurable(config['configurable']),
            defaults=defaults,
            create_defaults=defaults,
        )
        return {
            'configurable': self.format_configurable(checkpoint=instance),
        }

    def put_writes(self, config, writes, task_id, task_path = ""):
        instance = LangchainCheckpoint.objects \
            .filter(**self.format_configurable(config['configurable'])) \
            .first()
        if not instance:
            return

        pending_writes = self.serde.loads_typed((instance.pending_writes_type, instance.pending_writes)) if instance.pending_writes else []
        for w in pending_writes:
            if w['task_id'] == task_id and w['task_path'] == task_path:
                # Update existing write
                w['writes'].extend(writes)
                break
        else:
            # Add new pending write
            pending_writes.append({
                'task_id': task_id,
                'task_path': task_path,
                'writes': writes,
            })
        instance.pending_writes_type, instance.pending_writes = self.serde.dumps_typed(pending_writes)
        instance.save()

    def delete_thread(self, thread_id: str) -> None:
        LangchainCheckpoint.objects \
            .filter(thread_id=thread_id) \
            .delete()

    @sync_to_async
    def aget_tuple(self, *args, **kwargs):
        out = self.get_tuple(*args, **kwargs)
        return out

    @sync_to_async
    def alist(self, *args, **kwargs):
        return list(self.list(*args, **kwargs))

    @sync_to_async
    def aput(self, *args, **kwargs):
        return self.put(*args, **kwargs)

    @sync_to_async
    def aput_writes(self, *args, **kwargs):
        return self.put_writes(*args, **kwargs)

    @sync_to_async
    def adelete_thread(self, *args, **kwargs):
        return self.delete_thread(*args, **kwargs)
