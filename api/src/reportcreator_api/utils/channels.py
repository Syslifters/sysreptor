from adrf.views import APIView as AsyncAPIView
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from channels_postgres.core import PostgresChannelLayer
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from reportcreator_api.pentests.models.collab import CollabEvent
from reportcreator_api.utils.utils import omit_keys


class CustomizedPostgresChannelLayer(PostgresChannelLayer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove incompatible options
        self.db_params = omit_keys(self.db_params, ['context', 'cursor_factory'])


class ConsumerHttpFallbackView(AsyncAPIView):
    consumer_class = None
    permission_classes = []  # Permission check is handled in the consumer

    async def get_consumer(self):
        # Initialize consumer
        consumer = self.consumer_class()
        consumer.scope = {
            'user': self.request.user,
            'session': self.request.session,
            'path': self.request.path,
            'url_route': {'kwargs': self.kwargs, 'args': self.args},
        }
        consumer.channel_layer = get_channel_layer(consumer.channel_layer_alias)

        # Check permissions
        if not (await sync_to_async(consumer.has_permission)()):
            raise PermissionDenied()
        return consumer

    async def get(self, request, *args, **kwargs):
        consumer = await self.get_consumer()
        data = await consumer.get_initial_message()
        return Response(data=data)

    async def post(self, request, *args, **kwargs):
        consumer = await self.get_consumer()

        version = request.data.get('version', None)
        if not version:
            raise ValidationError('version is missing')

        # Dispatch incoming messages
        for msg in request.data.get('messages', []):
            msg_type = msg.get('type')
            if msg_type == 'collab.ping':
                continue  # Ignore pings, they are only relevant for websocket keepalive
            await consumer.receive_json(msg)

        # Get events since version (including responses to incoming messages)
        events = CollabEvent.objects \
            .filter(version__gt=version) \
            .filter(related_id=consumer.related_id) \
            .order_by('created')
        events = consumer.filter_path(events)
        events = [e async for e in events]

        return Response(data={
            'version': max([version] + [e.version for e in events]),
            'events': [{
                'type': e.type,
                'path': e.path,
                'client_id': e.client_id,
                'version': e.version,
                **e.data,
            } for e in events],
            'clients': await sync_to_async(consumer.get_client_infos)(),
        })

# TODO: Websocket fallback to HTTP
# * [x] API
#   * [x] GET /ws/.../fallback/ => return initial message (full data, version, clients)
#       * [x] check permissions
#       * [x] call consumer.get_initial_message()
#   * [x] POST /ws/.../fallback/?version=123 => send messages, return all messages since version (+ clients)
#       * [x] check permissions
#       * [x] proxy all messages to consumer.receive_*()
#       * [x] return all messages since version (+ client infos)
# * [ ] frontend
#   * [ ] connect to websocket x2
#   * [ ] on connection error: fallback to HTTP
#   * [ ] collab.ts refactoring
#   * [ ] do not send awareness messages
#   * [ ] warning toast when using HTTP fallback
# * [x] tests
#   * [x] test_api
#   * [x] test_collab
