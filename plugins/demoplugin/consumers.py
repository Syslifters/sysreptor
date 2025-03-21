from sysreptor.pentests.collab.consumer_base import WebsocketConsumerBase
from sysreptor.pentests.models import PentestProject


class DemoPluginConsumer(WebsocketConsumerBase):
    async def get_related_id(self):
        return self.scope['url_route']['kwargs']['project_pk']

    @property
    def group_name(self):
        return f'hellowebsocket_{self.related_id}'

    def has_permission(self, action, **kwargs):
        project = self.get_project()
        if not self.user or not project:
            return False
        return True

    def get_project(self, prefetch_related=False):
        return PentestProject.objects \
            .only_permitted(self.user) \
            .filter(id=self.related_id) \
            .first()

    async def connect(self):
        await super().connect()

        # Send an initial message when the client connects
        await self.send_json({
            'type': 'init',
            'client_id': self.client_id,
            'message': 'You successfully connected to the websocket consumer',
        })

    async def receive_json(self, content, **kwargs):
        match content.get('type'):
            case 'echo':
                # Send the message back to the client
                await self.send_json(content)
            case 'broadcast':
                # Broadcast the message to all consumers in the group
                await self.channel_layer.group_send(self.group_name, content | {
                    'client_id': self.client_id,
                })
            case _:
                raise ValueError(f'Invalid message type: {content.get("type")}')

    async def broadcast(self, event):
        # Send broadcasted events to the client
        await self.send_json(event)

