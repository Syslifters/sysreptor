import contextlib

import pytest
import pytest_asyncio
from asgiref.sync import sync_to_async
from sysreptor.tests.mock import (
    create_project,
    create_user,
    websocket_client,
)

from ..apps import DemoPluginConfig

PLUGIN_ID = DemoPluginConfig.plugin_id
URL_NAMESPACE = DemoPluginConfig.label


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio()
class TestDemoPluginWebsocketConsumer:
    @pytest_asyncio.fixture(autouse=True)
    async def setUp(self):
        @sync_to_async()
        def setup_db():
            self.user1 = create_user()
            self.user2 = create_user()
            self.project = create_project(members=[self.user1, self.user2])
        await setup_db()
        async with self.ws_connect(self.user1) as self.client1, \
                   self.ws_connect(self.user2) as self.client2:
            yield

    @contextlib.asynccontextmanager
    async def ws_connect(self, user, consume_init=True):
        async with websocket_client(path=f'/api/plugins/{PLUGIN_ID}/ws/projects/{self.project.id}/hellowebsocket/', user=user) as consumer:
            if consume_init:
                init = await consumer.receive_json_from()
                assert init.get('type') == 'init'
                consumer.init = init
                consumer.client_id = init['client_id']

            yield consumer

    async def test_echo(self):
        await self.client1.send_json_to({'type': 'echo', 'message': 'Hello'})
        response = await self.client1.receive_json_from()
        assert response == {'type': 'echo', 'message': 'Hello'}
        await self.client2.receive_nothing()

    async def test_broadcast(self):
        msg = {'type': 'broadcast', 'message': 'Hello'}
        await self.client1.send_json_to(msg)
        msg |= {'client_id': self.client1.client_id}
        assert await self.client1.receive_json_from() == msg
        assert await self.client2.receive_json_from() == msg
