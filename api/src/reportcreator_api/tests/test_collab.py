import pytest
import pytest_asyncio
import contextlib
from datetime import timedelta
from asgiref.sync import sync_to_async
from django.urls import reverse
from django.contrib.auth.models import AnonymousUser
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter

from reportcreator_api.pentests.models.collab import CollabEventType
from reportcreator_api.pentests.models.project import ProjectMemberInfo
from reportcreator_api.tests.mock import api_client, create_project, create_user, mock_time
from reportcreator_api.conf.urls import websocket_urlpatterns
from reportcreator_api.utils.text_transformations import ChangeSet, EditorSelection, SelectionRange, Update, rebase_updates


class TestTextTransformations:
    def assert_changes(self, text, changes, expected):
        change_set = ChangeSet.from_dict(changes)
        res = change_set.apply(text)
        assert res == expected
        return res

    def test_changes(self):
        operations = [
            # Write first line (without linebreak)
            {'changes': [[0, "line1"]], 'expected': 'line1'},
            # Insert newline
            {'changes': [5, [0, '', '']], 'expected': 'line1\n'},
            # Write second line
            {'changes': [6, [0, 'line2']], 'expected': 'line1\nline2'},
            # Insert multiline
            {'changes': [11, [0, '', 'line3', 'line4', '']], 'expected': 'line1\nline2\nline3\nline4\n'},
            # Prepend line
            {'changes': [[0, 'line0', ''], 24], 'expected': 'line0\nline1\nline2\nline3\nline4\n'},
            # Delete lines
            {'changes': [11, [12], 7], 'expected': 'line0\nline1\nline4\n'},
            # Replace char
            {'changes': [16, [1, '2'], 1], 'expected': 'line0\nline1\nline2\n'},
            # Replace multiple chars (at different positions)
            {'changes': [[1, 'L'], 5, [1, 'L'], 5, [1, 'L'], 5], 'expected': 'Line0\nLine1\nLine2\n'},
            # Delete multiple chars (at different positions)
            {'changes': [1, [1], 1, [1], 3, [1], 1, [1], 3, [1], 1, [1], 2], 'expected': 'Ln0\nLn1\nLn2\n'},
            # Type character for character
            {'changes': [12, [0, 'L']], 'expected': 'Ln0\nLn1\nLn2\nL'},
            {'changes': [13, [0, 'n']], 'expected': 'Ln0\nLn1\nLn2\nLn'},
            {'changes': [14, [0, '4']], 'expected': 'Ln0\nLn1\nLn2\nLn4'},
            {'changes': [14, [1]], 'expected': 'Ln0\nLn1\nLn2\nLn'},
            {'changes': [14, [0, '3']], 'expected': 'Ln0\nLn1\nLn2\nLn3'},
        ]

        # Loading and serialization
        for op in operations:
            assert ChangeSet.from_dict(op['changes']).to_dict() == op['changes']

        # Apply changes in order
        text = ''
        for op in operations:
            text = self.assert_changes(text=text, changes=op['changes'], expected=op['expected'])

        # Combine changes
        combined_change = ChangeSet.from_dict(operations[0]['changes'])
        for op in operations[1:]:
            combined_change = combined_change.compose(ChangeSet.from_dict(op['changes']))
            assert combined_change.apply('') == op['expected']

    @pytest.mark.parametrize(['text', 'change1', 'change2', 'expected'], [
        ('line1\nline2\n', [4, [1, '0'], 7], [10, [1, '1'], 1], 'line0\nline1\n'),
        ('line1\nline2\n', [5, [0, '', ''], 7], [7, [3], 2], 'line1\n\nl2\n'),
        ('line1\nline2\n', [5, [7]], [9, [0, 'e'], 3], 'line1e'),
        ('ABCDE', [1, [1], 3], [3, [1], 1], 'ACE'),
        ('AD', [1, [0, 'B'], 1], [1, [0, 'C'], 1], 'ABCD'),
    ])
    def test_operational_transform(self, text, change1, change2, expected):
        c1 = ChangeSet.from_dict(change1)
        c2 = ChangeSet.from_dict(change2)
        assert c1.compose(c2.map(c1)).apply(text) == expected
        assert c2.compose(c1.map(c2, True)).apply(text) == expected
        
        text1 = c1.apply(text)
        updates = rebase_updates(updates=[Update(client_id='c2', version=2, changes=c2)], over=[Update(client_id='c1', version=1, changes=c1)])
        assert len(updates) == 1
        assert updates[0].changes.apply(text1) == expected

        # Rebase already applied changes
        assert rebase_updates(updates=[Update(client_id='c2', version=2, changes=c2)], over=[Update(client_id='c1', version=1, changes=c1), Update(client_id='c2', version=2, changes=c2)]) == []

    @pytest.mark.parametrize(['selection', 'change', 'expected'], [
        # Cursor
        ([{'anchor': 10, 'head': 10}], [5, [0, 'inserted before'], 20], [{'anchor': 25, 'head': 25}]),
        ([{'anchor': 10, 'head': 10}], [5, [5, ''], 20], [{'anchor': 5, 'head': 5}]),  # deleted before
        ([{'anchor': 10, 'head': 10}], [20, [0, 'inserted after']], [{'anchor': 10, 'head': 10}]),
        ([{'anchor': 20, 'head': 20}], [0, [15, 'replaced before'], 20], [{'anchor': 20, 'head': 20}]),
        ([{'anchor': 10, 'head': 10}], [5, [0, 'inserted over'], 20], [{'anchor': 23, 'head': 23}]),
        ([{'anchor': 10, 'head': 10}], [5, [10, ''], 20], [{'anchor': 5, 'head': 5}]),  # delete over
        # Single range
        ([{'anchor': 10, 'head': 15}], [5, [0, 'inserted before'], 20], [{'anchor': 25, 'head': 30}]),
        ([{'anchor': 10, 'head': 15}], [5, [5, ''], 20], [{'anchor': 5, 'head': 10}]),  # deleted before
        ([{'anchor': 10, 'head': 15}], [20, [0, 'inserted after']], [{'anchor': 10, 'head': 15}]),
        ([{'anchor': 10, 'head': 15}], [5, [0, 'inserted before'], 30, [0, 'inserted after']], [{'anchor': 25, 'head': 30}]),
        ([{'anchor': 10, 'head': 20}], [15, [0, 'inserted inside'], 20], [{'anchor': 10, 'head': 35}]),
        ([{'anchor': 10, 'head': 40}], [15, [15, 'replaced inside'], 40], [{'anchor': 10, 'head': 40}]),
        ([{'anchor': 10, 'head': 20}], [12, [5, ''], 20], [{'anchor': 10, 'head': 15}]), # delete inside
        ([{'anchor': 10, 'head': 20}], [5, [10, ''], 20], [{'anchor': 5, 'head': 10}]), # delete overlapping start
        ([{'anchor': 10, 'head': 20}], [15, [10, ''], 20], [{'anchor': 10, 'head': 15}]), # delete overlapping end
        ([{'anchor': 10, 'head': 20}], [5, [20, ''], 20], [{'anchor': 5, 'head': 5}]), # delete whole range
        # Multiple ranges
        ([{'anchor': 10, 'head': 15}, {'anchor': 20, 'head': 25}], [5, [0, 'inserted before'], 20], [{'anchor': 25, 'head': 30}, {'anchor': 35, 'head': 40}]),
        ([{'anchor': 10, 'head': 15}, {'anchor': 20, 'head': 25}], [5, [5, ''], 20], [{'anchor': 5, 'head': 10}, {'anchor': 15, 'head': 20}]),  # deleted before
        ([{'anchor': 10, 'head': 15}, {'anchor': 20, 'head': 25}], [17, [0, 'inserted between'], 20], [{'anchor': 10, 'head': 15}, {'anchor': 36, 'head': 41}]),
    ])
    def test_selection_mapping(self, selection, change, expected):
        selection = EditorSelection(main=0, ranges=[SelectionRange.from_dict(r) for r in selection])
        change = ChangeSet.from_dict(change)
        expected = EditorSelection(main=0, ranges=[SelectionRange.from_dict(r) for r in expected])
        actual = selection.map(change)
        assert actual == expected


@contextlib.asynccontextmanager
async def ws_connect(path, user):
    consumer = WebsocketCommunicator(
        application=URLRouter(websocket_urlpatterns),
        path=path,
    )
    consumer.scope['user'] = user

    try:
        # Connect
        connected, _ = await consumer.connect()
        assert connected

        # Consume initial message
        init = await consumer.receive_json_from()
        assert init.get('type') == 'init'
        setattr(consumer, 'init', init)
        setattr(consumer, 'client_id', init['client_id'])

        # Consume collab.connect message
        connect = await consumer.receive_json_from()
        assert connect.get('type') == 'collab.connect'
        assert connect.get('client_id') == init['client_id']

        yield consumer
    finally:
        await consumer.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestCollaborativeTextEditing:
    @pytest_asyncio.fixture(autouse=True)
    async def setUp(self):
        def setup_db():
            self.user1 = create_user()
            self.user2 = create_user()
            self.project = create_project(members=[self.user1, self.user2], notes_kwargs=[{'text': 'AB'}])
            self.note = self.project.notes.all()[0]
        await sync_to_async(setup_db)()

        async with ws_connect(path=f'/ws/pentestprojects/{self.project.id}/notes/', user=self.user1) as self.client1, \
                   ws_connect(path=f'/ws/pentestprojects/{self.project.id}/notes/', user=self.user2) as self.client2:
            await self.client1.receive_json_from() # collab.connect client2
            yield
    
    async def test_concurrent_updates(self):
        # Concurrent updates of same version
        event_base = {'type': CollabEventType.UPDATE_TEXT, 'path': f'notes.{self.note.note_id}.text', 'version': self.client1.init['version']}
        await self.client1.send_json_to(event_base | {'updates': [{'changes': [1, [0, '1'], 1]}]})
        await self.client2.send_json_to(event_base | {'updates': [{'changes': [1, [0, '2'], 1]}]})

        await self.client1.receive_json_from()
        version = (await self.client1.receive_json_from())['version']
        assert version > self.client1.init['version']

        await self.note.arefresh_from_db()
        assert self.note.text == 'A12B'

        # Third update after both previous changes (using updated version)
        await self.client1.send_json_to(event_base | {'version': version, 'updates': [{'changes': [4, [0, '3']]}]})
        await self.client1.receive_json_from()

        await self.note.arefresh_from_db()
        assert self.note.text == 'A12B3'

    async def test_rebase_updates(self):
        event_base = {'type': CollabEventType.UPDATE_TEXT, 'path': f'notes.{self.note.note_id}.text', 'version': self.client1.init['version']}
        updates = [{'changes': [1, [0, '1'], 1]}, {'changes': [2, [0, '2'], 1]}, {'changes': [3, [0, '3'], 1]}, {'changes': [4, [0, '4'], 1]}]
        await self.client1.send_json_to(event_base | {'updates': updates[:2]})
        await self.client1.send_json_to(event_base | {'updates': updates})

        res1 = await self.client1.receive_json_from()
        assert res1['updates'] == updates[:2]
        res2 = await self.client1.receive_json_from()
        assert res2['updates'] == updates[2:]

        await self.note.arefresh_from_db()
        assert self.note.text == 'A1234B'

    # TODO: test rebase selection
    # TODO: test collab.awareness


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestProjectNotesDbSync:
    @pytest_asyncio.fixture(autouse=True)
    async def setUp(self):
        def setup_db():
            self.user1 = create_user()
            self.user2 = create_user()
            self.project = create_project(members=[self.user1, self.user2], notes_kwargs=[{'checked': None, 'icon_emoji': None, 'text': 'ABC'}])
            self.note = self.project.notes.all()[0]
            self.note_path_prefix = f'notes.{self.note.note_id}'
            self.api_client1 = api_client(self.user1)
        await sync_to_async(setup_db)()

        async with ws_connect(path=f'/ws/pentestprojects/{self.project.id}/notes/', user=self.user1) as self.client1, \
                   ws_connect(path=f'/ws/pentestprojects/{self.project.id}/notes/', user=self.user2) as self.client2:
            await self.client1.receive_json_from() # collab.connect client2
            yield

    async def refresh_data(self):
        await self.note.arefresh_from_db()

    async def test_update_key(self):
        event = {'type': CollabEventType.UPDATE_KEY, 'path': self.note_path_prefix + '.icon_emoji', 'value': '👍'}
        await self.client1.send_json_to(event)

        # Websocket messages sent to clients
        res1 = await self.client1.receive_json_from()
        res2 = await self.client2.receive_json_from()
        for k, v in (event | {'client_id': self.client1.client_id}).items():
            assert res1[k] == res2[k] == v

        # Changes synced to DB
        await self.refresh_data()
        assert self.note.icon_emoji == event['value']

        # History entry created
        assert await self.note.history.acount() == 2
        note_h = await self.note.history.order_by('-history_date').afirst()
        assert note_h.history_type == '~'
        assert note_h.icon_emoji == self.note.icon_emoji

    async def test_update_text(self):
        event = {'type': CollabEventType.UPDATE_TEXT, 'path': self.note_path_prefix + '.text', 'updates': [{'changes': [3, [0, 'D']]}]}
        await self.client1.send_json_to(event | {'version': self.client1.init['version']})

        # Websocket messages sent to clients
        res1 = await self.client1.receive_json_from()
        res2 = await self.client2.receive_json_from()
        for k, v in (event | {'client_id': self.client1.client_id}).items():
            assert res1[k] == res2[k] == v
        
        # Changes synced to DB
        await self.refresh_data()
        assert self.note.text == 'ABCD'

        # History entry created
        assert await self.note.history.acount() == 2
        note_h = await self.note.history.order_by('-history_date').afirst()
        assert note_h.history_type == '~'
        assert note_h.text == self.note.text

    async def test_create_sync(self):
        res_api = await sync_to_async(self.api_client1.post)(
            path=reverse('projectnotebookpage-list', kwargs={'project_pk': self.project.id}), 
            data={'title': 'new', 'text': 'new'})
        # Create event
        res1 = await self.client1.receive_json_from()
        res2 = await self.client2.receive_json_from()
        for k, v in ({'type': CollabEventType.CREATE, 'path': f'notes.{res_api.data["id"]}', 'value': res_api.data, 'client_id': None}).items():
            assert res1[k] == res2[k] == v

        # Sort event
        res1 = await self.client1.receive_json_from()
        res2 = await self.client2.receive_json_from()
        for k, v in ({'type': CollabEventType.SORT, 'path': 'notes', 'client_id': None}).items():
            assert res1[k] == res2[k] == v

    async def test_delete_sync(self):
        await sync_to_async(self.note.delete)()
        res1 = await self.client1.receive_json_from()
        res2 = await self.client2.receive_json_from()
        for k, v in ({'type': CollabEventType.DELETE, 'path': self.note_path_prefix, 'client_id': None}).items():
            assert res1[k] == res2[k] == v

    async def test_update_key_sync(self):
        await sync_to_async(self.api_client1.patch)(
            path=reverse('projectnotebookpage-detail', kwargs={'project_pk': self.project.id, 'id': self.note.note_id}), 
            data={'checked': True, 'title': 'updated'})
        
        r1_1 = await self.client1.receive_json_from()
        r1_2 = await self.client1.receive_json_from()
        res1 = {r1_1['path']: r1_1, r1_2['path']: r1_2}

        r2_1 = await self.client2.receive_json_from()
        r2_2 = await self.client2.receive_json_from()
        res2 = {r2_1['path']: r2_1, r2_2['path']: r2_2}

        for k, v in ({'type': CollabEventType.UPDATE_KEY, 'path': self.note_path_prefix + '.title', 'value': 'updated', 'client_id': None}).items():
            assert res1[self.note_path_prefix + '.title'][k] == res2[self.note_path_prefix + '.title'][k] == v
        for k, v in ({'type': CollabEventType.UPDATE_KEY, 'path': self.note_path_prefix + '.checked', 'value': True, 'client_id': None}).items():
            assert res1[self.note_path_prefix + '.checked'][k] == res2[self.note_path_prefix + '.checked'][k] == v

    async def test_sort_sync(self):
        res = await sync_to_async(self.api_client1.post)(
            path=reverse('projectnotebookpage-sort', kwargs={'project_pk': self.project.id}),
            data=[{'id': self.note.note_id, 'order': 1, 'parent': None}])
        res1 = await self.client1.receive_json_from()
        res2 = await self.client2.receive_json_from()

        for k, v in ({'type': CollabEventType.SORT, 'path': 'notes', 'client_id': None, 'sort': res.data}).items():
            assert res1[k] == res2[k] == v

    async def test_member_removed_write(self):
        await ProjectMemberInfo.objects.filter(project=self.project, user=self.user1).adelete()

        await self.client1.send_json_to({'type': CollabEventType.UPDATE_KEY, 'path': self.note_path_prefix + '.checked', 'value': True})
        res = await self.client1.receive_output()
        assert res['type'] == 'websocket.close'
        
    async def test_member_removed_read(self):
        await ProjectMemberInfo.objects.filter(project=self.project, user=self.user1).adelete()

        with mock_time(after=timedelta(minutes=2)):
            await self.client2.send_json_to({'type': CollabEventType.UPDATE_KEY, 'path': self.note_path_prefix + '.checked', 'value': True})
            await self.client2.receive_json_from()

            res1 = await self.client1.receive_output()
            assert res1['type'] == 'websocket.close'

    async def test_project_readonly_write(self):
        self.project.readonly = True
        await self.project.asave()

        await self.client1.send_json_to({'type': CollabEventType.UPDATE_KEY, 'path': self.note_path_prefix + '.checked', 'value': True})
        res = await self.client1.receive_output()
        assert res['type'] == 'websocket.close'


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestConsumerPermissions:
    async def ws_connect(self, path, user):
        consumer = WebsocketCommunicator(
            application=URLRouter(websocket_urlpatterns),
            path=path,
        )
        consumer.scope |= {
            'user': user,
            'session': {'admin_permissions_enabled': True},
        }
        connected, _ = await consumer.connect()
        await consumer.disconnect()
        return connected

    @pytest.mark.parametrize(['expected', 'user_name', 'project_name'], [
        (True, 'member', 'project'),
        (True, 'admin', 'project'),
        (False, 'unauthorized', 'project'),
        (False, 'anonymous', 'project'),
        (False, 'member', 'readonly'),
        (False, 'admin', 'readonly'),
    ])
    async def test_project_note_permissions(self, expected, user_name, project_name):
        def setup_db():
            user_member = create_user()
            users = {
                'member': user_member,
                'admin': create_user(is_superuser=True),
                'unauthorized': create_user(),
                'anonymous': AnonymousUser(),
            }
            projects = {
                'project': create_project(members=[user_member]),
                'readonly': create_project(members=[user_member], readonly=True),
            }
            return users[user_name], projects[project_name]
        user, project = await sync_to_async(setup_db)()
        assert await self.ws_connect(f'/ws/pentestprojects/{project.id}/notes/', user) == expected

    @pytest.mark.parametrize(['expected', 'user_name'], [
        (True, 'self'),
        (False, 'admin'),
        (False, 'unauthorized'),
        (False, 'anonymous'),
    ])
    async def test_user_notes_permissions(self, expected, user_name):
        def setup_db():
            user_notes = create_user()
            users = {
                'self': user_notes,
                'admin': create_user(is_superuser=True),
                'unauthorized': create_user(),
                'anonymous': AnonymousUser(),
            }
            return users[user_name], user_notes    
        user, user_notes = await sync_to_async(setup_db)()
        assert await self.ws_connect(f'/ws/pentestusers/{user_notes.id}/notes/', user) == expected
