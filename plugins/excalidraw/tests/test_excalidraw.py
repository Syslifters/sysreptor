import io

import pytest
import pytest_asyncio
from asgiref.sync import sync_to_async
from django.contrib.auth.models import AnonymousUser
from sysreptor.pentests.import_export import export_projects, import_projects
from sysreptor.pentests.models import CollabEventType
from sysreptor.tests.mock import (
    create_project,
    create_user,
    override_configuration,
    websocket_client,
)

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


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio()
class TestExcalidrawCollabPermissions:
    async def ws_connect(self, project, user):
        async with websocket_client(path=f'/api/plugins/{PLUGIN_ID}/ws/projects/{project.id}/excalidraw/', user=user, connect=False) as consumer:
            can_read, _ = await consumer.connect()
            can_write = False
            if can_read:
                await consumer.receive_json_from()  # collab.init
                await consumer.receive_json_from()  # collab.connect

                await consumer.send_json_to({'type': 'collab.update_excalidraw', 'elements': []})
                msg = await consumer.receive_output()
                can_write = msg['type'] != 'websocket.close'

            return can_read, can_write
    
    @pytest.mark.parametrize(('user_name', 'project_name', 'expected_read', 'expected_write'), [
        ('member', 'project', True, True),
        ('guest', 'project', True, False),
        ('admin', 'project', True, True),
        ('unauthorized', 'project', False, False),
        ('anonymous', 'project', False, False),
        ('member', 'readonly', True, False),
        ('guest', 'readonly', True, False),
        ('admin', 'readonly', True, False),
    ])
    async def test_permissions(self, user_name, project_name, expected_read, expected_write):
        def setup_db():
            user_member = create_user()
            user_guest = create_user(is_guest=True)
            users = {
                'member': user_member,
                'guest': user_guest,
                'admin': create_user(is_superuser=True),
                'unauthorized': create_user(),
                'anonymous': AnonymousUser(),
            }
            user = users[user_name]
            if user.is_superuser:
                user.admin_permissions_enabled = True

            projects = {
                'project': create_project(members=[user_member, user_guest]),
                'readonly': create_project(members=[user_member, user_guest], readonly=True),
            }
            project = projects[project_name]
            return user, project
        
        with override_configuration(GUEST_USERS_CAN_EDIT_PROJECTS=False):
            user, project = await sync_to_async(setup_db)()
            can_read, can_write = await self.ws_connect(project, user)
            assert can_read == expected_read
            assert can_write == expected_write


@pytest.mark.django_db()
class TestExcalidrawExportImport:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.project = create_project()
        self.excalidraw_data = ProjectExcalidrawData.objects.create(
            project=self.project,
            elements=[{'id': 'e1', 'type': 'rectangle', 'x': 0, 'y': 0}],
        )

    def perform_export_import(self, export_all=True):
        archive = io.BytesIO(b''.join(export_projects([self.project], export_all=export_all)))
        self.project.refresh_from_db()
        imported = import_projects(archive)
        assert len(imported) == 1
        return imported[0]

    def test_export_import_excalidraw_data(self):
        p = self.perform_export_import(export_all=True)
        e = ProjectExcalidrawData.objects.get(project=p)
        assert e.elements == self.excalidraw_data.elements

    def test_export_only_project(self):
        p = self.perform_export_import(export_all=False)
        assert ProjectExcalidrawData.objects.filter(project=p).count() == 0

    def test_export_missing_excalidraw_data(self):
        self.excalidraw_data.delete()
        p = self.perform_export_import(export_all=True)
        assert ProjectExcalidrawData.objects.filter(project=p).count() == 0
