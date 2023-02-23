import gc
from pathlib import Path
from celery import Celery, signals
from celery.backends.base import Backend
from celery.backends.rpc import RPCBackend, ResultConsumer
from kombu import pools
from django.conf import settings


class SecureWorkerFixup:
    """
    Restart celery worker container after every task.
    """

    def __init__(self, app: Celery) -> None:
        self.app = app
        if settings.CELERY_SECURE_WORKER:
            self.install()
    
    def install(self):
        signals.task_prerun.connect(self.on_task_prerun)

    def on_task_prerun(self, task, *args, **kwargs):
        # Restart worker
        self.app.control.shutdown(destination=[task.request.hostname])

         # Close broker connection pool
        self.app.pool.force_close_all()
        pools.reset()

        # Remove credentials
        settings.CELERY_BROKER_URL = None
        if settings.CELERY_BROKER_URL_FILE:
            Path(settings.CELERY_BROKER_URL_FILE).unlink()
        gc.collect()


class CustomRPCResultConsumer(ResultConsumer):
    def start(self, initial_task_id, no_ack=True, **kwargs):
        self._connection = self.backend.connection()
        initial_queue = self._create_binding(initial_task_id)
        self._consumer = self.Consumer(
            channel=self._connection.default_channel,
            queues=[initial_queue],
            callbacks=[self.on_state_change],
            no_ack=no_ack,
            accept=self.accept
        )
        self._consumer.consume()


class CustomRPCBackend(RPCBackend):
    """
    Celery RPC result backend which uses a separate amqp connection for sending results.
    """

    ResultConsumer = CustomRPCResultConsumer

    def connection(self):
        return self.app.amqp.Connection(
            self.url.replace('reportcreator_api.tasks.rendering.celery_worker:CustomRPCBackend', 'pyamqp'),
            connect_timeout=self.app.conf.broker_connection_timeout
        )

    def store_result(self, task_id, result, state, traceback=None, request=None, **kwargs):
        routing_key, correlation_id = self.destination_for(task_id, request)
        if not routing_key:
            return
        
        with self.connection() as conn:
            with self.app.amqp.Producer(conn) as producer:
                producer.publish(
                    self._to_result(task_id, state, result, traceback, request),
                    exchange=self.exchange,
                    routing_key=routing_key,
                    correlation_id=correlation_id,
                    serializer=self.serializer,
                    retry=True, retry_policy=self.retry_policy,
                    declare=self.on_reply_declare(task_id),
                    delivery_mode=self.delivery_mode,
                )
        return result

    def as_uri(self, include_password=True):
        return Backend.as_uri(self, include_password)
