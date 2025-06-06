import pytest
import pytest_asyncio
from asgiref.sync import sync_to_async
from sysreptor.pentests.models import CollabEventType
from sysreptor.tests.mock import create_project, create_user, websocket_client

from ..apps import ExcalidrawPluginConfig
from ..models import ProjectExcalidrawData

PLUGIN_ID = ExcalidrawPluginConfig.plugin_id


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio()
class TestExcalidrawCollab:
    @pytest_asyncio.fixture(autouse=True)
    async def setUp(self):
        def setup_db():
            self.user1 = create_user()
            self.user2 = create_user()
            self.project = create_project(members=[self.user1, self.user2])
        await sync_to_async(setup_db)()
    
    def assert_events_equal(self, actual, expected):
        for k, v in expected.items():
            assert actual[k] == v
        return actual

    async def test_excalidraw_collab(self):
        async with websocket_client(path=f'/api/plugins/{PLUGIN_ID}/ws/projects/{self.project.id}/excalidraw/', user=self.user1) as client1, \
                   websocket_client(path=f'/api/plugins/{PLUGIN_ID}/ws/projects/{self.project.id}/excalidraw/', user=self.user2) as client2:
            init1 = self.assert_events_equal(await client1.receive_json_from(), {'type': CollabEventType.INIT})
            client1.client_id = init1['client_id']
            self.assert_events_equal(await client1.receive_json_from(), {'type': CollabEventType.CONNECT, 'client_id': client1.client_id})

            init2 = self.assert_events_equal(await client2.receive_json_from(), {'type': CollabEventType.INIT})
            client2.client_id = init2['client_id']
            self.assert_events_equal(await client2.receive_json_from(), {'type': CollabEventType.CONNECT, 'client_id': client2.client_id})
            self.assert_events_equal(await client1.receive_json_from(), {'type': CollabEventType.CONNECT, 'client_id': client2.client_id})

            # Test event broadcasting
            event = {
                'type': 'collab.update_excalidraw',
                'client_id':  client1.client_id,
                'elements': [{'id': 'e1', 'type': 'rectangle', 'x': 0, 'y': 0}],
            }
            await client1.send_json_to(event)
            self.assert_events_equal(await client1.receive_json_from(), event)
            self.assert_events_equal(await client2.receive_json_from(), event)

            # Test disconnect
            await client2.disconnect()
            self.assert_events_equal(await client1.receive_json_from(), {'type': CollabEventType.DISCONNECT, 'client_id': client2.client_id})

    async def test_sync_to_db(self):
        data = await ProjectExcalidrawData.objects.acreate(
            project=self.project,
            elements=[{'id': 'e1', 'type': 'rectangle', 'x': 0, 'y': 0}],
        )

        async with websocket_client(path=f'/api/plugins/{PLUGIN_ID}/ws/projects/{self.project.id}/excalidraw/', user=self.user1) as client:
            # DB data sent in init event
            self.assert_events_equal(await client.receive_json_from(), {'type': CollabEventType.INIT})
            self.assert_events_equal(await client.receive_json_from(), {'type': CollabEventType.CONNECT})

            # Save update to DB
            new_elements = data.elements + [{'id': 'e2', 'type': 'rectangle', 'x': 10, 'y': 10}]
            event = {
                'type': 'collab.update_excalidraw',
                'elements': new_elements,
                'syncall': True,  # sync to all clients
            }
            await client.send_json_to(event)
            self.assert_events_equal(await client.receive_json_from(), event)

            # Verify data saved to DB
            db_data = await ProjectExcalidrawData.objects.aget(project=self.project)
            assert db_data.elements == new_elements