import asyncio
import logging
from typing import Any

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import close_old_connections, connections
from taskiq import TaskiqMiddleware
from taskiq.brokers.inmemory_broker import InMemoryBroker
from taskiq.decor import AsyncTaskiqDecoratedTask
from taskiq.message import TaskiqMessage
from taskiq.result import TaskiqResult
from taskiq_redis import RedisStreamBroker, RedisStreamSentinelBroker


class DjangoDBMiddleware(TaskiqMiddleware):
    """Close Django DB connections around each task, like request/response handling."""

    async def pre_execute(self, message: TaskiqMessage) -> TaskiqMessage:
        logging.info(f'Executing background task {message.task_name}')
        await _close_old_connections()
        return message

    async def post_execute(self, message: TaskiqMessage, result: TaskiqResult) -> None:
        await _close_old_connections()

    async def on_error(self, message: TaskiqMessage, result: TaskiqResult, exception: BaseException) -> None:
        await _close_old_connections()


@sync_to_async
def _close_old_connections():
    if not connections['default'].in_atomic_block:
        close_old_connections()


def _create_broker():
    if settings.TASKIQ_ALWAYS_EAGER:
        # Run tasks inline in the current process. Used in unit tests.
        return InMemoryBroker(await_inplace=True)

    redis_config = dict(settings.REDIS_CONNECTION_CONFIG or {})
    if redis_config.get('sentinels') and redis_config.get('master_name'):
        return RedisStreamSentinelBroker(
            sentinels=[tuple(s) for s in redis_config.pop('sentinels')],
            master_name=redis_config.pop('master_name'),
            maxlen=10000,
            **redis_config,
        )
    elif redis_url := redis_config.pop('address', settings.REDIS_URL):
        return RedisStreamBroker(
            url=redis_url,
            maxlen=10000,
            **redis_config,
        )
    else:
        # Run tasks in a background task in the current process.
        # Fallback if redis is not available.
        return InMemoryBroker(await_inplace=False)


broker = _create_broker() \
    .with_middlewares(DjangoDBMiddleware())


_broker_started = False
_broker_start_lock = asyncio.Lock()


async def ensure_broker_started():
    global _broker_started
    if _broker_started or broker.is_worker_process:
        return
    async with _broker_start_lock:
        # Another waiter may have completed startup before we acquired the lock.
        if not _broker_started:
            await broker.startup()
            _broker_started = True


class BackgroundAsyncTaskiqDecoratedTask(AsyncTaskiqDecoratedTask):
    """
    Taskiq task that enqueues on call from request workers.

    Workers execute ``original_func`` directly; client code can ``await task(...)``.
    """

    reraise_on_enqueue_error: bool = True

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        if self.broker.is_worker_process:
            return await self.original_func(*args, **kwargs)

        try:
            await ensure_broker_started()
            await self.kiq(*args, **kwargs)
        except Exception:
            logging.exception(f'Error while enqueuing background task {self.task_name}')
            if self.reraise_on_enqueue_error:
                raise


def background_task(task_name: str, reraise_on_enqueue_error: bool = True, **labels: Any):
    """Register a background task; ``await task(...)`` enqueues it outside worker processes."""
    def decorator(func):
        old_decorator_class = broker.decorator_class
        broker.decorator_class = BackgroundAsyncTaskiqDecoratedTask
        try:
            task = broker.task(task_name=task_name, **{
                'ack_type': 'when_received',
             } | labels)(func)
            task.reraise_on_enqueue_error = reraise_on_enqueue_error
            return task
        finally:
            broker.decorator_class = old_decorator_class
    return decorator
