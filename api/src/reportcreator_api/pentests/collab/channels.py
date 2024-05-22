import logging

from adrf.views import APIView as AsyncAPIView
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from channels_postgres.core import PostgresChannelLayer
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from reportcreator_api.pentests.models.collab import CollabEvent
from reportcreator_api.utils.utils import omit_keys


class CustomizedPostgresChannelLayer(PostgresChannelLayer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove incompatible options
        self.db_params = omit_keys(self.db_params, ['context', 'cursor_factory'])


class ConsumerHttpFallbackSerializer(serializers.Serializer):
    version = serializers.FloatField(min_value=1)
    client_id = serializers.CharField()
    messages = serializers.ListField(child=serializers.JSONField())

    def validate_client_id(self, value):
        if not value or not value.startswith(str(self.context['request'].user.id)):
            raise ValidationError('Invalid client_id')
        return value


class ConsumerHttpFallbackView(AsyncAPIView):
    schema = None
    consumer_class = None
    permission_classes = []  # Permission check is handled in the consumer

    async def get_consumer(self, action=None, client_id=None):
        # Initialize consumer
        consumer = self.consumer_class()
        consumer.scope = {
            'user': self.request.user,
            'session': self.request.session,
            'path': self.request.path,
            'url_route': {'kwargs': self.kwargs, 'args': self.args},
            'client_id': client_id,
        }
        consumer.channel_layer = get_channel_layer(consumer.channel_layer_alias)

        # Check permissions
        if not (await sync_to_async(consumer.has_permission)(action=action)):
            raise PermissionDenied()
        return consumer

    async def get(self, request, *args, **kwargs):
        consumer = await self.get_consumer(action='read')
        data = await consumer.get_initial_message()
        return Response(data=data)

    async def post(self, request, *args, **kwargs):
        serializer = ConsumerHttpFallbackSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        version = data['version']

        consumer = await self.get_consumer(action='write', client_id=data['client_id'])

        # Dispatch incoming messages
        error = None
        for msg in request.data.get('messages', []):
            msg_type = msg.get('type')
            if msg_type == 'collab.ping':
                continue  # Ignore pings, they are only relevant for websocket keepalive
            try:
                await consumer.receive_json(msg)
            except ValidationError:
                continue
            except Exception as ex:
                logging.exception(ex)
                # Raise error after processing all events
                error = ex
        if error:
            raise error

        # Get events since version (including responses to incoming messages)
        events = CollabEvent.objects \
            .filter(version__gt=version) \
            .filter(related_id=consumer.related_id) \
            .order_by('created')
        events = consumer.filter_path(events)
        events = [e async for e in events]

        return Response(data={
            'version': max([version] + [e.version for e in events]),
            'messages': [{
                'type': e.type,
                'path': e.path,
                'client_id': e.client_id,
                'version': e.version,
                **e.data,
            } for e in events],
            'clients': await sync_to_async(consumer.get_client_infos)(),
        })

