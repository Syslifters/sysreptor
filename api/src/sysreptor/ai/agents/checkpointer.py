"""
PostgreSQL checkpointer for LangGraph using Django ORM.
Stores conversation state and enables thread persistence.
"""
import json
from collections.abc import Iterator, Sequence
from typing import Any

from asgiref.sync import sync_to_async
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Subquery
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    WRITES_IDX_MAP,
    BaseCheckpointSaver,
    ChannelVersions,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    get_checkpoint_id,
    get_serializable_checkpoint_metadata,
)

from sysreptor.ai.models import LangchainCheckpoint
from sysreptor.utils.utils import copy_keys


class DjangoModelCheckpointer(BaseCheckpointSaver):
    def format_configurable(self, checkpoint: Checkpoint | LangchainCheckpoint) -> dict[str, Any]:
        return {
            k: str(v) for k, v in copy_keys(checkpoint, ['thread_id', 'checkpoint_ns', 'checkpoint_id']).items()
            if v is not None
        }

    def format_checkpoint_tuple(self, checkpoint: LangchainCheckpoint) -> CheckpointTuple:
        pending_writes = []
        if checkpoint.pending_writes:
            for pw in self.serde.loads_typed((checkpoint.pending_writes_type, checkpoint.pending_writes)):
                task_id = pw.get('task_id')
                for c, v in pw.get('writes', []):
                    pending_writes.append((task_id, c, v))

        return CheckpointTuple(
            config={
                'configurable': self.format_configurable(checkpoint=checkpoint),
            },
            checkpoint=self.serde.loads_typed((checkpoint.checkpoint_type, checkpoint.checkpoint)),
            metadata=json.loads(checkpoint.metadata or {}),
            parent_config={
                'configurable': {
                    'thread_id': str(checkpoint.thread_id),
                    'checkpoint_ns': checkpoint.checkpoint_ns or '',
                    'checkpoint_id': str(checkpoint.parent_checkpoint_id),
                },
            } if checkpoint.parent_checkpoint_id else None,
            pending_writes=pending_writes,
        )

    def get_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        thread_id = config['configurable'].get('thread_id')
        if not thread_id:
            return None

        filters = {
            'thread_id': str(thread_id),
            'checkpoint_ns': config['configurable'].get('checkpoint_ns', '') or '',
        }
        qs = LangchainCheckpoint.objects.filter(**filters)
        if checkpoint_id := get_checkpoint_id(config):
            qs = qs.filter(checkpoint_id=checkpoint_id)
        else:
            qs = qs.order_by('-created')

        checkpoint = qs.first()
        if not checkpoint:
            return None
        return self.format_checkpoint_tuple(checkpoint=checkpoint)

    def list(self, config: RunnableConfig, *, filter: dict[str, Any] | None = None, before: RunnableConfig | None = None, limit: int | None = None) -> Iterator[CheckpointTuple]:
        filters = {k: str(v) for k, v in copy_keys(config['configurable'], ['thread_id', 'checkpoint_ns']).items() if v is not None}
        if 'thread_id' not in filters:
            return iter([])
        if 'checkpoint_ns' not in filters:
            filters['checkpoint_ns'] = ''

        qs = LangchainCheckpoint.objects \
            .filter(**filters) \
            .order_by('-created')
        if before and before['configurable'].get('checkpoint_id'):
            qs = qs.filter(created__lt=Subquery(
                LangchainCheckpoint.objects
                    .filter(**filters)
                    .filter(checkpoint_id=before['configurable']['checkpoint_id'])
                    .values('created'),
                ))
        if limit:
            qs = qs[:limit]

        return [self.format_checkpoint_tuple(checkpoint=checkpoint) for checkpoint in qs]

    def put(self, config: RunnableConfig, checkpoint: Checkpoint, metadata: CheckpointMetadata, new_versions: ChannelVersions) -> RunnableConfig:
        thread_id = config['configurable'].get('thread_id')
        if not thread_id:
            raise ValueError('thread_id is required for checkpoint persistence')

        checkpoint_ns = config['configurable'].get('checkpoint_ns', '') or ''
        checkpoint_id = checkpoint['id']
        parent_checkpoint_id = config['configurable'].get('checkpoint_id')

        t, d = self.serde.dumps_typed(checkpoint)
        defaults = {
            'checkpoint_type': t,
            'checkpoint': d,
            'metadata': json.dumps(get_serializable_checkpoint_metadata(config=config, metadata=metadata), cls=DjangoJSONEncoder).encode(),
            'parent_checkpoint_id': parent_checkpoint_id,
        }
        LangchainCheckpoint.objects.update_or_create(
            thread_id=str(thread_id),
            checkpoint_ns=checkpoint_ns,
            checkpoint_id=checkpoint_id,
            defaults=defaults,
            create_defaults=defaults,
        )
        return {
            'configurable': {
                'thread_id': str(thread_id),
                'checkpoint_ns': checkpoint_ns,
                'checkpoint_id': str(checkpoint_id),
            },
        }

    def put_writes(self, config: RunnableConfig, writes: Sequence[tuple[str, Any]], task_id: str, task_path: str = '') -> None:
        thread_id = config['configurable'].get('thread_id')
        checkpoint_id = config['configurable'].get('checkpoint_id')
        if not thread_id or not checkpoint_id:
            return

        checkpoint_ns = config['configurable'].get('checkpoint_ns', '') or ''
        instance = LangchainCheckpoint.objects.filter(
            thread_id=str(thread_id),
            checkpoint_ns=checkpoint_ns,
            checkpoint_id=checkpoint_id,
        ).first()
        if not instance:
            return

        pending_writes = self.serde.loads_typed((instance.pending_writes_type, instance.pending_writes)) if instance.pending_writes else []

        # Index existing writes for this task like InMemorySaver / WRITES_IDX_MAP
        existing_by_idx: dict[int, dict] = {}
        for pw in pending_writes:
            if pw.get('task_id') != task_id or pw.get('task_path') != task_path:
                continue
            for idx, (channel, _value) in enumerate(pw.get('writes', [])):
                write_idx = WRITES_IDX_MAP.get(channel, idx)
                existing_by_idx[write_idx] = pw

        task_writes = next(
            (pw for pw in pending_writes if pw.get('task_id') == task_id and pw.get('task_path') == task_path),
            None,
        )
        if task_writes is None:
            task_writes = {
                'task_id': task_id,
                'task_path': task_path,
                'writes': [],
            }
            pending_writes.append(task_writes)

        for idx, (channel, value) in enumerate(writes):
            write_idx = WRITES_IDX_MAP.get(channel, idx)
            # Special channels (negative idx) always overwrite; others are write-once
            if write_idx >= 0 and write_idx in existing_by_idx:
                continue
            if write_idx < 0:
                # Replace any previous write for this special channel on the task
                task_writes['writes'] = [
                    (c, v) for c, v in task_writes['writes']
                    if WRITES_IDX_MAP.get(c) != write_idx
                ]
            task_writes['writes'].append((channel, value))
            existing_by_idx[write_idx] = task_writes

        instance.pending_writes_type, instance.pending_writes = self.serde.dumps_typed(pending_writes)
        instance.save(update_fields=['pending_writes_type', 'pending_writes'])

    def delete_thread(self, thread_id: str) -> None:
        LangchainCheckpoint.objects \
            .filter(thread_id=thread_id) \
            .delete()

    @sync_to_async
    def aget_tuple(self, *args, **kwargs):
        return self.get_tuple(*args, **kwargs)

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
