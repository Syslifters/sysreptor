import asyncio
import contextlib
import json
import logging
import time
from collections.abc import AsyncIterator
from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from django.utils import timezone
from rest_framework.exceptions import APIException

from sysreptor.ai.models import AgentRunStatus, ChatThread

logger = logging.getLogger(__name__)

HEARTBEAT_TTL_SECONDS = 30
HEARTBEAT_INTERVAL_SECONDS = 5
KEEPALIVE_INTERVAL_SECONDS = 15


class AiEventType:
    STREAM = 'ai.stream'
    SYNC_REQUEST = 'ai.sync'
    CANCEL_REQUEST = 'ai.cancel'


class ThreadBusyError(APIException):
    status_code = 409
    default_detail = 'An agent run is already active on this thread.'
    default_code = 'thread_busy'

    def __init__(self, active_run_id: UUID | str | None = None, detail=None):
        self.active_run_id = str(active_run_id) if active_run_id else None
        super().__init__(detail={
            'detail': detail or self.default_detail,
            'active_run': self.active_run_id,
            'code': self.default_code,
        })


class PendingEventBuffer:
    """In-memory wire events not yet in the LangGraph checkpoint (text coalesced)."""

    def __init__(self):
        self._events: dict[str, dict] = {}
        self._order: list[str] = []

    @staticmethod
    def _key(event: dict) -> str | None:
        etype = event.get('type')
        if not etype:
            return None
        content = event.get('content')
        eid = content.get('id') if isinstance(content, dict) else None
        return f'{etype}:{eid}' if eid is not None else etype

    @staticmethod
    def _copy(event: dict) -> dict:
        content = event.get('content')
        if isinstance(content, dict | list):
            content = type(content)(content)
        out = {'type': event.get('type'), 'content': content}
        if 'subagent' in event:
            out['subagent'] = event['subagent']
        return out

    def _put(self, key: str, event: dict) -> None:
        if key not in self._events:
            self._order.append(key)
        self._events[key] = event

    def apply(self, event: dict) -> None:
        match event.get('type'):
            case 'text':
                self._apply_text(event)
            case 'tool_call_status':
                self._apply_tool_call_status(event)
            case _:
                if key := self._key(event):
                    self._put(key, self._copy(event))

    def _apply_text(self, event: dict) -> None:
        content = event.get('content') or {}
        key = self._key(event)
        if not key:
            return
        if content.get('replace') or key not in self._events:
            self._put(key, self._copy(event))
            return
        stored = self._events[key]['content']
        for field in ('text', 'reasoning'):
            if field in content:
                stored[field] = (stored.get(field) or '') + (content[field] or '')

    def _apply_tool_call_status(self, event: dict) -> None:
        content = event.get('content') or {}
        key = self._key({'type': 'tool_call', 'content': {'id': content.get('id')}})
        if not key or key not in self._events:
            return
        content = self._events[key]['content']
        content.update(event.get('content') or {})

    def events(self, covered: list|set|None = None, *, replace: bool|None = True) -> list[dict]:
        covered = covered or ()
        out = []
        for key in self._order:
            event = self._copy(self._events[key])
            if event.get('type') == 'text' and replace is not None:
                event['content'] = {**event['content'], 'replace': replace}
            content = event.get('content')
            eid = content.get('id') if isinstance(content, dict) else None
            if eid and eid in covered:
                continue
            out.append(event)
        return out

    def clear(self) -> None:
        self._events.clear()
        self._order.clear()


def group_name_stream(run_id: UUID | str) -> str:
    return f'ai.stream.{run_id}'


def group_name_control(run_id: UUID | str) -> str:
    return f'ai.control.{run_id}'


async def send_ai_stream_event(run_id: UUID | str, event: dict) -> None:
    try:
        await get_channel_layer().group_send(group_name_stream(run_id), {
            'type': AiEventType.STREAM,
            'event': event,
        })
    except Exception:
        logger.exception('Failed to group_send AI stream event for run %s', run_id)


async def send_ai_stream_event_to_channel(channel: str, event: dict) -> None:
    try:
        await get_channel_layer().send(channel, {
            'type': AiEventType.STREAM,
            'event': event,
        })
    except Exception:
        logger.exception('Failed to send AI stream event to channel %s', channel)


async def send_ai_control(run_id: UUID | str, message: dict) -> None:
    try:
        await get_channel_layer().group_send(group_name_control(run_id), message)
    except Exception:
        logger.exception('Failed to send control message for run %s', run_id)


async def throttle_ai_stream_events(stream: AsyncIterator[dict], interval=0.5) -> AsyncIterator[dict]:
    buffer = PendingEventBuffer()
    last_flush = 0.0
    aiter = stream.__aiter__()
    next_event = asyncio.ensure_future(aiter.__anext__())

    def flush() -> list[dict]:
        nonlocal last_flush
        events = buffer.events(replace=None)
        buffer.clear()
        if events:
            last_flush = time.monotonic()
        return events

    def should_flush_immediately(event: dict|None) -> bool:
        if not event or not isinstance(event, dict):
            return False
        content = event.get('content')
        if isinstance(content, dict) and content.get('replace'):
            return True
        if event.get('type') == 'text':
            return False
        return True

    try:
        while True:
            timeout = None
            if buffer._events:
                timeout = max(0.0, interval - (time.monotonic() - last_flush))

            done, _ = await asyncio.wait({next_event}, timeout=timeout)
            event = None
            if done:
                try:
                    event = next_event.result()
                    buffer.apply(event)
                    next_event = asyncio.ensure_future(aiter.__anext__())
                except StopAsyncIteration:
                    break

            flush_immediately = should_flush_immediately(event)
            if not done or flush_immediately or time.monotonic() - last_flush >= interval:
                for flushed in flush():
                    yield flushed
                if flush_immediately:
                    # Skip timeout for next event (flush on leading edge)
                    # such that the next event/message starts immediately and is not delayed by the interval.
                    last_flush = 0.0

        # On exit: drain pending events
        for event in flush():
            yield event
    finally:
        if not next_event.done():
            next_event.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await next_event


class AgentRunWorker:
    """
    Background worker for one agent run: drive the stream, serve the control
    channel (sync / cancel), and watch ownership / access.
    """

    def __init__(
        self,
        thread: ChatThread,
        *,
        agent: str,
        model: str | None,
        input_data: Any,
        context: dict | None = None,
    ):
        self.thread = thread
        self.run_id = thread.run_id
        self.agent = agent
        self.model = model
        self.input_data = input_data
        self.context = context or {}
        self.pending = PendingEventBuffer()
        self.lock = asyncio.Lock()
        self.result: dict = {'status': AgentRunStatus.COMPLETED}
        self._agent_task: asyncio.Task | None = None
        self.channel_layer = get_channel_layer()

    async def run(self) -> None:
        control_task = asyncio.create_task(self.control_loop())
        self._agent_task = agent_task = asyncio.create_task(self.drive())
        error_reason = None
        try:
            error_reason = await self.watch()
            await agent_task
        except asyncio.CancelledError:
            self.result = {
                'status': AgentRunStatus.ERROR,
                'error': error_reason or 'Agent aborted',
            }
        except Exception:
            logger.exception('Agent run failed')
            self.result = {
                'status': AgentRunStatus.ERROR,
                'error': self.result.get('error') or 'Unexpected error',
            }
        else:
            if error_reason is not None:
                self.result = {'status': AgentRunStatus.ERROR, 'error': error_reason}
        finally:
            if not agent_task.done():
                agent_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await agent_task
            control_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await control_task
            await end_run(
                thread=self.thread,
                status=self.result['status'],
                error=self.result.get('error'),
                interrupts=self.result.get('interrupts'),
            )

    async def send(self, event: dict) -> None:
        async with self.lock:
            self.pending.apply(event)
            await send_ai_stream_event(self.run_id, event)

    async def drive(self) -> None:
        from sysreptor.ai.agents import agent_stream, get_agent

        agent_instance = await sync_to_async(get_agent)(self.agent)
        async for event in throttle_ai_stream_events(agent_stream(
            agent=agent_instance,
            input=self.input_data,
            thread=self.thread,
            context=self.context,
            model=self.model,
        )):
            etype = event.get('type')
            if etype == 'interrupt':
                self.result['status'] = AgentRunStatus.INTERRUPTED
                self.result['interrupts'] = event.get('content') or []
            elif etype == 'error':
                self.result['status'] = AgentRunStatus.ERROR
                self.result['error'] = event.get('content')
            await self.send(event)

    async def watch(self) -> str | None:
        agent_task = self._agent_task
        if agent_task is None:
            return None

        while not agent_task.done():
            done, _ = await asyncio.wait({agent_task}, timeout=HEARTBEAT_INTERVAL_SECONDS)
            if done:
                return None

            try:
                current = await ChatThread.objects \
                    .filter(id=self.thread.id) \
                    .afirst()
                if current is None:
                    agent_task.cancel()
                    return 'thread deleted'
                if current.run_id != self.run_id or current.run_status != AgentRunStatus.RUNNING:
                    # Cancel or stale-marking already published run_status
                    agent_task.cancel()
                    return None

                await ChatThread.objects \
                    .filter(id=self.thread.id) \
                    .filter(run_id=self.run_id) \
                    .filter(run_status=AgentRunStatus.RUNNING) \
                    .aupdate(run_heartbeat_at=timezone.now())
            except Exception:
                logger.exception('Agent run watch error')

        return None

    async def control_loop(self) -> None:
        group = group_name_control(self.run_id)
        channel = await self.channel_layer.new_channel()
        await self.channel_layer.group_add(group, channel)
        try:
            while True:
                msg = await self.channel_layer.receive(channel)
                if isinstance(msg, dict):
                    await self.dispatch(msg)
        finally:
            with contextlib.suppress(Exception):
                await self.channel_layer.group_discard(group, channel)

    async def dispatch(self, message: dict) -> None:
        msg_type = message.get('type')
        if not isinstance(msg_type, str):
            return
        handler = getattr(self, msg_type.replace('.', '_'), None)
        if handler is None:
            return
        await handler(message)

    async def ai_sync(self, message: dict) -> None:
        # Filter with the subscriber's snapshot covered set (no second history load).
        reply_channel = message.get('reply_channel')
        async with self.lock:
            events = self.pending.events(message.get('covered'))

        for ev in events:
            if reply_channel:
                await send_ai_stream_event_to_channel(reply_channel, ev)
            else:
                await send_ai_stream_event(self.run_id, ev)

    async def ai_cancel(self, message: dict) -> None:
        if self._agent_task and not self._agent_task.done():
            self._agent_task.cancel()


async def end_run(thread: ChatThread, status: str, error: str|None = None, interrupts: list|None = None) -> bool:
    """
    Atomically move a run from RUNNING to a terminal status and publish run_status.
    Returns True if this call performed the transition.
    """
    updated = await ChatThread.objects \
        .filter(id=thread.id) \
        .filter(run_id=thread.run_id) \
        .filter(run_status=AgentRunStatus.RUNNING) \
        .aupdate(run_status=status)
    if not updated:
        return False
    thread.run_status = status

    content: dict = {'status': status}
    if error:
        content['error'] = error
    if interrupts:
        content['interrupts'] = interrupts
    await send_ai_stream_event(thread.run_id, {'type': 'run_status', 'content': content})
    return True


async def ensure_thread_not_stale(thread: ChatThread) -> None:
    if thread.run_status != AgentRunStatus.RUNNING or not thread.run_id:
        return
    cutoff = timezone.now() - timedelta(seconds=HEARTBEAT_TTL_SECONDS)
    if thread.run_heartbeat_at is not None and thread.run_heartbeat_at >= cutoff:
        return
    await end_run(thread=thread, status=AgentRunStatus.ERROR, error='Agent aborted')


async def start_run(thread: ChatThread) -> UUID:
    await ensure_thread_not_stale(thread)

    run_id = uuid4()
    now = timezone.now()
    claimed = await ChatThread.objects \
        .filter(id=thread.id) \
        .exclude(run_status=AgentRunStatus.RUNNING) \
        .aupdate(
            run_id=run_id,
            run_status=AgentRunStatus.RUNNING,
            run_heartbeat_at=now,
        )
    if not claimed:
        active = await ChatThread.objects \
            .filter(id=thread.id) \
            .values_list('run_id', flat=True) \
            .afirst()
        raise ThreadBusyError(active_run_id=active)

    thread.run_id = run_id
    thread.run_status = AgentRunStatus.RUNNING
    thread.run_heartbeat_at = now
    return run_id


async def cancel_run(thread: ChatThread) -> UUID | None:
    await ensure_thread_not_stale(thread)
    if thread.run_status != AgentRunStatus.RUNNING or not thread.run_id:
        return None
    run_id = thread.run_id
    if await end_run(thread=thread, status=AgentRunStatus.CANCELLED):
        await send_ai_control(run_id, {'type': AiEventType.CANCEL_REQUEST})
        return run_id
    return None


async def subscribe_thread(thread: ChatThread) -> AsyncIterator[dict | None]:
    """
    Yield SSE-ready events for a thread: snapshot, then live tail.
    Yields None as a keepalive marker.
    """
    from sysreptor.ai.agents import get_agent, get_chat_history

    await ensure_thread_not_stale(thread)
    thread = await ChatThread.objects.select_related('user', 'project').aget(pk=thread.pk)

    layer = get_channel_layer()
    channel = None
    group = None
    # Join the active run group before the snapshot so events between snapshot
    # and sync are not missed.
    if thread.run_status == AgentRunStatus.RUNNING and thread.run_id:
        group = group_name_stream(thread.run_id)
        channel = await layer.new_channel()
        await layer.group_add(group, channel)
    try:
        history = await sync_to_async(get_chat_history)(
            agent=get_agent('project_ask'),
            thread=thread,
            include_pending_tools=True,
        )
        covered = history.get('covered') or []
        yield {
            'type': 'snapshot',
            'content': {
                'thread_id': str(thread.id),
                'run_id': str(thread.run_id) if thread.run_id else None,
                'run_status': thread.run_status,
                'messages': history.get('messages') or [],
                'interrupts': history.get('interrupts') or [],
            },
        }

        if thread.run_status != AgentRunStatus.RUNNING or not thread.run_id or channel is None:
            content: dict = {'status': thread.run_status}
            interrupts = history.get('interrupts') or []
            if interrupts:
                content['interrupts'] = interrupts
            yield {'type': 'run_status', 'content': content}
            return

        # Pass snapshot covered to the worker so sync skips history events.
        await send_ai_control(thread.run_id, {
            'type': AiEventType.SYNC_REQUEST,
            'reply_channel': channel,
            'covered': list(covered),
        })

        while True:
            try:
                msg = await asyncio.wait_for(
                    layer.receive(channel),
                    timeout=KEEPALIVE_INTERVAL_SECONDS,
                )
            except TimeoutError:
                yield None
                continue
            if not isinstance(msg, dict) or msg.get('type') != AiEventType.STREAM:
                continue
            event = msg.get('event')
            if not isinstance(event, dict):
                continue
            yield event
            if event.get('type') == 'run_status':
                return
    finally:
        if channel and group:
            with contextlib.suppress(Exception):
                await layer.group_discard(group, channel)


async def to_subscriber_sse(thread: ChatThread):
    async for event in subscribe_thread(thread):
        if event is None:
            yield b': keepalive\n\n'
            continue
        event_type = event.get('type', 'message')
        yield f'event: {event_type}\ndata: {json.dumps(event)}\n\n'.encode()
        if event_type == 'run_status':
            return
