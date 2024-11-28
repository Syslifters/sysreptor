"""
Unit tests for plugin functionality.

To run this test, execute the following command:
cd sysreptor/dev
docker compose run --rm -e ENABLED_PLUGINS=demoplugin api pytest sysreptor_plugins/demoplugin
"""

import contextlib

import pytest
import pytest_asyncio
from asgiref.sync import sync_to_async
from django.urls import reverse
from reportcreator_api.tests.mock import (
    api_client,
    create_project,
    create_user,
    websocket_client,
)

from ..app import DemoPluginConfig
from ..models import DemoPluginModel

PLUGIN_ID = DemoPluginConfig.plugin_id
URL_NAMESPACE = DemoPluginConfig.label


@pytest.mark.django_db()
class TestDemoPluginApi:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user()
        self.client = api_client(self.user)
        self.demopluginmodel = DemoPluginModel.objects.create(name='Test')
    
    def test_retrieve(self):
        res = self.client.get(reverse(URL_NAMESPACE + ':demopluginmodel-detail', kwargs={'pk': self.demopluginmodel.id}))
        assert res.status_code == 200
        assert res.data['id'] == str(self.demopluginmodel.id)
        assert res.data['name'] == self.demopluginmodel.name
    
    def test_create(self):
        res = self.client.post(reverse(URL_NAMESPACE + ':demopluginmodel-list'), data={'name': 'New'})
        assert res.status_code == 201
        obj = DemoPluginModel.objects.get(id=res.data['id'])
        assert obj.name == 'New'
    
    def test_update(self):
        res = self.client.patch(reverse(URL_NAMESPACE + ':demopluginmodel-detail', kwargs={'pk': self.demopluginmodel.id}), data={'name': 'Updated'})
        assert res.status_code == 200
        self.demopluginmodel.refresh_from_db()
        assert self.demopluginmodel.name == 'Updated'

    def test_delete(self):
        res = self.client.delete(reverse(URL_NAMESPACE + ':demopluginmodel-detail', kwargs={'pk': self.demopluginmodel.id}))
        assert res.status_code == 204
        assert not DemoPluginModel.objects.filter(id=self.demopluginmodel.id).exists()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio()
class TestDemoPluginWebsocketConsumer:
    @pytest_asyncio.fixture(autouse=True)
    async def setUp(self):
        @sync_to_async
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
