"""
PostgreSQL checkpointer for LangGraph using Django ORM.
Stores conversation state and enables thread persistence.
"""
import json
import random
from collections.abc import Iterator, Mapping, Sequence
from typing import Any
from uuid import UUID

from asgiref.sync import sync_to_async
from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection
from django.db.models import Q, Subquery
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    WRITES_IDX_MAP,
    BaseCheckpointSaver,
    ChannelVersions,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    DeltaChannelHistory,
    get_checkpoint_id,
    get_serializable_checkpoint_metadata,
)
from langgraph.checkpoint.serde.types import _DeltaSnapshot

from sysreptor.ai.models import (
    ChatThread,
    LangchainCheckpoint,
    LangchainCheckpointBlob,
    LangchainCheckpointWrite,
)
from sysreptor.utils.utils import copy_keys


def _is_inline_primitive(value: Any) -> bool:
    return value is None or isinstance(value, str | int | float | bool)


def _as_uuid(value: Any) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))


class DjangoModelCheckpointer(BaseCheckpointSaver):
    def get_next_version(self, current: str | None, channel: None) -> str:
        if current is None:
            current_v = 0
        elif isinstance(current, int):
            current_v = current
        else:
            current_v = int(str(current).split('.')[0])
        next_v = current_v + 1
        next_h = random.random()  # noqa: S311
        return f'{next_v:032}.{next_h:016}'

    def format_configurable(self, checkpoint: Checkpoint | LangchainCheckpoint) -> dict[str, Any]:
        return {
            k: str(v) for k, v in copy_keys(checkpoint, ['thread_id', 'checkpoint_ns', 'checkpoint_id']).items()
            if v is not None
        }

    def _dump_metadata(self, config: RunnableConfig, metadata: CheckpointMetadata) -> bytes:
        return json.dumps(
            get_serializable_checkpoint_metadata(config=config, metadata=metadata),
            cls=DjangoJSONEncoder,
        ).encode()

    def _load_metadata(self, metadata: Any) -> dict[str, Any]:
        if not metadata:
            return {}
        if isinstance(metadata, dict):
            return metadata
        if isinstance(metadata, bytes | memoryview):
            return json.loads(bytes(metadata))
        if isinstance(metadata, str):
            return json.loads(metadata)
        return {}

    def _load_blobs(self, *, thread_id: str, checkpoint_ns: str, channel_versions: Mapping[str, Any]) -> dict[str, Any]:
        if not channel_versions:
            return {}

        q = Q()
        for channel, version in channel_versions.items():
            q |= Q(channel=channel, version=str(version))

        rows = LangchainCheckpointBlob.objects \
            .filter(thread_id=str(thread_id)) \
            .filter(checkpoint_ns=checkpoint_ns) \
            .filter(q)

        values: dict[str, Any] = {}
        for row in rows:
            if row.type == 'empty':
                continue
            values[row.channel] = self.serde.loads_typed((row.type, row.blob or b''))
        return values

    def _load_writes(self, *, thread_id: str, checkpoint_ns: str, checkpoint_id: str) -> list[tuple[str, str, Any]]:
        rows = LangchainCheckpointWrite.objects \
            .filter(thread_id=str(thread_id)) \
            .filter(checkpoint_ns=checkpoint_ns) \
            .filter(checkpoint_id=_as_uuid(checkpoint_id)) \
            .order_by('task_id', 'idx')
        return [(row.task_id, row.channel, self.serde.loads_typed((row.type, row.blob))) for row in rows]

    def format_checkpoint_tuple(self, checkpoint: LangchainCheckpoint) -> CheckpointTuple:
        checkpoint_data = dict(checkpoint.checkpoint or {})
        channel_versions = checkpoint_data.get('channel_versions') or {}
        channel_values = dict(checkpoint_data.get('channel_values') or {})
        channel_values.update(self._load_blobs(
            thread_id=str(checkpoint.thread_id),
            checkpoint_ns=checkpoint.checkpoint_ns or '',
            channel_versions=channel_versions,
        ))
        checkpoint_data['channel_values'] = channel_values

        return CheckpointTuple(
            config={
                'configurable': self.format_configurable(checkpoint=checkpoint),
            },
            checkpoint=checkpoint_data,
            metadata=self._load_metadata(checkpoint.metadata),
            parent_config={
                'configurable': {
                    'thread_id': str(checkpoint.thread_id),
                    'checkpoint_ns': checkpoint.checkpoint_ns or '',
                    'checkpoint_id': str(checkpoint.parent_checkpoint_id),
                },
            } if checkpoint.parent_checkpoint_id else None,
            pending_writes=self._load_writes(
                thread_id=str(checkpoint.thread_id),
                checkpoint_ns=checkpoint.checkpoint_ns or '',
                checkpoint_id=str(checkpoint.checkpoint_id),
            ),
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

    def _split_channel_values(self, checkpoint: Checkpoint) -> tuple[dict[str, Any], dict[str, Any]]:
        copy = checkpoint.copy()
        copy['channel_values'] = dict(copy.get('channel_values') or {})
        blob_values: dict[str, Any] = {}
        for k, v in list(copy['channel_values'].items()):
            if isinstance(v, _DeltaSnapshot):
                blob_values[k] = copy['channel_values'].pop(k)
                copy['channel_values'][k] = True
            elif _is_inline_primitive(v):
                pass
            else:
                blob_values[k] = copy['channel_values'].pop(k)
        return copy, blob_values

    def put(self, config: RunnableConfig, checkpoint: Checkpoint, metadata: CheckpointMetadata, new_versions: ChannelVersions) -> RunnableConfig:
        thread_id = config['configurable'].get('thread_id')
        if not thread_id:
            raise ValueError('thread_id is required for checkpoint persistence')

        checkpoint_ns = config['configurable'].get('checkpoint_ns', '') or ''
        checkpoint_id = checkpoint['id']
        parent_checkpoint_id = config['configurable'].get('checkpoint_id')

        slimmed, blob_values = self._split_channel_values(checkpoint)
        defaults = {
            'checkpoint': slimmed,
            'metadata': self._dump_metadata(config, metadata),
            'parent_checkpoint_id': parent_checkpoint_id,
        }
        LangchainCheckpoint.objects.update_or_create(
            thread_id=str(thread_id),
            checkpoint_ns=checkpoint_ns,
            checkpoint_id=checkpoint_id,
            defaults=defaults,
            create_defaults=defaults,
        )

        blob_rows = []
        for channel, version in new_versions.items():
            if channel not in blob_values:
                continue
            type_tag, blob = self.serde.dumps_typed(blob_values[channel])
            blob_rows.append(LangchainCheckpointBlob(
                thread_id=str(thread_id),
                checkpoint_ns=checkpoint_ns,
                channel=channel,
                version=str(version),
                type=type_tag,
                blob=blob,
            ))
        if blob_rows:
            LangchainCheckpointBlob.objects.bulk_create(blob_rows, ignore_conflicts=True)

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
        upsert = all(channel in WRITES_IDX_MAP for channel, _ in writes)

        rows = []
        for idx, (channel, value) in enumerate(writes):
            type_tag, blob = self.serde.dumps_typed(value)
            rows.append(LangchainCheckpointWrite(
                thread_id=str(thread_id),
                checkpoint_ns=checkpoint_ns,
                checkpoint_id=_as_uuid(checkpoint_id),
                task_id=task_id,
                task_path=task_path,
                idx=WRITES_IDX_MAP.get(channel, idx),
                channel=channel,
                type=type_tag,
                blob=blob,
            ))

        if not rows:
            return

        if upsert:
            LangchainCheckpointWrite.objects.bulk_create(
                rows,
                update_conflicts=True,
                unique_fields=['thread', 'checkpoint_ns', 'checkpoint_id', 'task_id', 'idx'],
                update_fields=['task_path', 'channel', 'type', 'blob'],
            )
        else:
            LangchainCheckpointWrite.objects.bulk_create(rows, ignore_conflicts=True)

    def delete_thread(self, thread_id: str) -> None:
        ChatThread.objects.filter(id=thread_id).delete()

    def _load_ancestor_chain_page(self, *, thread_id: str, checkpoint_ns: str, start_checkpoint_id: str, limit: int) -> list[LangchainCheckpoint]:
        if limit <= 0:
            return []

        sql = """
            WITH RECURSIVE chain AS (
                SELECT id, parent_checkpoint_id, 0 AS depth
                FROM ai_langchaincheckpoint
                WHERE thread_id = %s::uuid
                  AND checkpoint_ns = %s
                  AND checkpoint_id = %s::uuid
                UNION ALL
                SELECT c.id, c.parent_checkpoint_id, chain.depth + 1
                FROM ai_langchaincheckpoint c
                INNER JOIN chain
                  ON c.checkpoint_id = chain.parent_checkpoint_id
                 AND c.thread_id = %s::uuid
                 AND c.checkpoint_ns = %s
                WHERE chain.parent_checkpoint_id IS NOT NULL
                  AND chain.depth + 1 < %s
            )
            SELECT id FROM chain ORDER BY depth
        """
        with connection.cursor() as cursor:
            cursor.execute(
                sql,
                [thread_id, checkpoint_ns, start_checkpoint_id, thread_id, checkpoint_ns, limit],
            )
            ordered_ids = [row[0] for row in cursor.fetchall()]
        if not ordered_ids:
            return []
        by_pk = LangchainCheckpoint.objects.in_bulk(ordered_ids)
        return [by_pk[pk] for pk in ordered_ids if pk in by_pk]

    def _prefetch_delta_page_writes(self, *, thread_id: str, checkpoint_ns: str, checkpoint_ids: Sequence[Any], channels: Sequence[str]) -> dict[Any, list[LangchainCheckpointWrite]]:
        writes_by_cid: dict[Any, list[LangchainCheckpointWrite]] = {cid: [] for cid in checkpoint_ids}
        if not checkpoint_ids:
            return writes_by_cid
        rows = LangchainCheckpointWrite.objects \
            .filter(thread_id=str(thread_id)) \
            .filter(checkpoint_ns=checkpoint_ns) \
            .filter(checkpoint_id__in=list(checkpoint_ids)) \
            .filter(channel__in=list(channels)) \
            .order_by('-task_id', '-idx')
        for write in rows:
            writes_by_cid.setdefault(write.checkpoint_id, []).append(write)
        return writes_by_cid

    def _prefetch_delta_page_blobs(self, *, thread_id: str, checkpoint_ns: str, ancestors: Sequence[LangchainCheckpoint], channels: Sequence[str]) -> dict[tuple[str, str], LangchainCheckpointBlob]:
        version_pairs: set[tuple[str, str]] = set()
        for row in ancestors:
            versions = (row.checkpoint or {}).get('channel_versions') or {}
            for ch in channels:
                if ch in versions:
                    version_pairs.add((ch, str(versions[ch])))
        if not version_pairs:
            return {}

        blob_q = Q()
        for channel, version in version_pairs:
            blob_q |= Q(channel=channel, version=version)
        blobs_by_key: dict[tuple[str, str], LangchainCheckpointBlob] = {}
        blobs = LangchainCheckpointBlob.objects \
            .filter(thread_id=str(thread_id)) \
            .filter(checkpoint_ns=checkpoint_ns) \
            .filter(blob_q)
        for blob in blobs:
            blobs_by_key[(blob.channel, blob.version)] = blob
        return blobs_by_key

    def get_delta_channel_history(self, *, config: RunnableConfig, channels: Sequence[str]) -> Mapping[str, DeltaChannelHistory]:
        # Match langgraph-checkpoint-postgres page size / depth caps for delta history walks.
        DELTA_PAGE_SIZE = 1024
        DELTA_MAX_DEPTH = 100_000

        if not channels:
            return {}

        thread_id = config['configurable'].get('thread_id')
        if not thread_id:
            return {c: {'writes': []} for c in channels}

        checkpoint_ns = config['configurable'].get('checkpoint_ns', '') or ''
        filters = {
            'thread_id': str(thread_id),
            'checkpoint_ns': checkpoint_ns,
        }
        qs = LangchainCheckpoint.objects.filter(**filters)
        if checkpoint_id := get_checkpoint_id(config):
            target = qs.filter(checkpoint_id=checkpoint_id).first()
        else:
            target = qs.order_by('-created').first()

        if not target or not target.parent_checkpoint_id:
            return {c: {'writes': []} for c in channels}

        collected_by_ch: dict[str, list] = {c: [] for c in channels}
        seed_by_ch: dict[str, Any] = {}
        remaining: set[str] = set(channels)
        visited: set[Any] = set()
        cursor_checkpoint_id = str(target.parent_checkpoint_id)
        depth_seen = 0

        while remaining and depth_seen < DELTA_MAX_DEPTH:
            page_limit = min(DELTA_PAGE_SIZE, DELTA_MAX_DEPTH - depth_seen)
            page = self._load_ancestor_chain_page(
                thread_id=str(thread_id),
                checkpoint_ns=checkpoint_ns,
                start_checkpoint_id=cursor_checkpoint_id,
                limit=page_limit,
            )
            if not page:
                break

            # Cycle detection across pages (CTE depth cap only covers one page).
            cycle = False
            unique_page: list[LangchainCheckpoint] = []
            for row in page:
                if row.checkpoint_id in visited:
                    cycle = True
                    break
                visited.add(row.checkpoint_id)
                unique_page.append(row)
            page = unique_page
            if not page:
                break

            page_cids = [row.checkpoint_id for row in page]
            writes_by_cid = self._prefetch_delta_page_writes(
                thread_id=str(thread_id),
                checkpoint_ns=checkpoint_ns,
                checkpoint_ids=page_cids,
                channels=list(remaining),
            )
            blobs_by_key = self._prefetch_delta_page_blobs(
                thread_id=str(thread_id),
                checkpoint_ns=checkpoint_ns,
                ancestors=page,
                channels=list(remaining),
            )

            for row in page:
                if not remaining:
                    break
                shell = row.checkpoint or {}
                channel_values = shell.get('channel_values') or {}
                channel_versions = shell.get('channel_versions') or {}

                for write in writes_by_cid.get(row.checkpoint_id, []):
                    if write.channel not in remaining:
                        continue
                    value = self.serde.loads_typed((write.type, write.blob))
                    collected_by_ch[write.channel].append((write.task_id, write.channel, value))

                for ch in list(remaining):
                    version = channel_versions.get(ch)
                    blob = blobs_by_key.get((ch, str(version))) if version is not None else None
                    has_blob = blob is not None and blob.type != 'empty'
                    has_inline = ch in channel_values
                    if not has_blob and not has_inline:
                        continue
                    if has_blob:
                        seed_by_ch[ch] = self.serde.loads_typed((blob.type, blob.blob or b''))
                    else:
                        seed_by_ch[ch] = channel_values[ch]
                    remaining.discard(ch)

            depth_seen += len(page)
            if cycle or not remaining or len(page) < page_limit:
                break
            next_parent = page[-1].parent_checkpoint_id
            if not next_parent:
                break
            cursor_checkpoint_id = str(next_parent)

        result: dict[str, DeltaChannelHistory] = {}
        for ch in channels:
            entry: DeltaChannelHistory = {'writes': list(reversed(collected_by_ch[ch]))}
            if ch in seed_by_ch:
                entry['seed'] = seed_by_ch[ch]
            result[ch] = entry
        return result

    @sync_to_async
    def aget_tuple(self, *args, **kwargs):
        return self.get_tuple(*args, **kwargs)

    @sync_to_async
    def aget_delta_channel_history(self, *args, **kwargs):
        return self.get_delta_channel_history(*args, **kwargs)

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
