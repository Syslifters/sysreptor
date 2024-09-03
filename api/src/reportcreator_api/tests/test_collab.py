import contextlib
import copy
import itertools
import json
from datetime import timedelta

import pytest
import pytest_asyncio
from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from django.conf import settings
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY
from django.contrib.auth.models import AnonymousUser
from django.core.files.base import ContentFile
from django.core.serializers.json import DjangoJSONEncoder
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.module_loading import import_string

from reportcreator_api.archive.import_export import export_notes
from reportcreator_api.conf.asgi import application
from reportcreator_api.pentests.collab.text_transformations import (
    ChangeSet,
    CollabStr,
    EditorSelection,
    SelectionRange,
    Update,
    rebase_updates,
)
from reportcreator_api.pentests.customfields.utils import (
    ensure_defined_structure,
    get_value_at_path,
    set_value_at_path,
)
from reportcreator_api.pentests.models import (
    CollabClientInfo,
    CollabEventType,
    PentestFinding,
    ProjectMemberInfo,
    ReportSection,
    ReviewStatus,
    collab_context,
)
from reportcreator_api.tests.mock import (
    api_client,
    create_comment,
    create_project,
    create_project_type,
    create_projectnotebookpage,
    create_shareinfo,
    create_user,
    mock_time,
)
from reportcreator_api.utils.utils import copy_keys


class TestTextTransformations:
    def assert_changes(self, text, changes, expected):
        change_set = ChangeSet.from_dict(changes)
        res = change_set.apply(text)
        assert res == expected
        return res

    def test_unicode_handling(self):
        s_raw = 'before 🤦🏼‍♂️ after'
        s = CollabStr(s_raw)
        # Encode/decode
        assert str(s) == s_raw
        # Length
        assert len(s) == 6 + 1 + 7 + 1 + 5
        # Index
        assert str(s[0]) == 'b'
        assert str(s[15]) == 'a'
        assert str(s[-2]) == 'e'
        assert str(s[-1]) == 'r'
        # Slice
        assert str(s[:6]) == 'before'
        assert str(s[-5:]) == 'after'
        assert str(s[15:]) == 'after'
        assert str(s[7:14]) == '🤦🏼‍♂️'
        assert str(s[:14]) == 'before 🤦🏼‍♂️'
        assert str(s[7:]) == '🤦🏼‍♂️ after'
        assert str(s[0:]) == s_raw
        assert str(s[:]) == s_raw
        assert str(s[:0]) == ''
        assert str(s[-1:]) == s_raw[-1:]
        assert str(s[:-1]) == s_raw[:-1]

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
            # Unicode characters
            {'changes': [15, [0, ' 🤦🏼‍♂️ ']], 'expected': 'Ln0\nLn1\nLn2\nLn3 🤦🏼‍♂️ '},
            {'changes': [24, [0, 'unicode']], 'expected': 'Ln0\nLn1\nLn2\nLn3 🤦🏼‍♂️ unicode'},
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

    @pytest.mark.parametrize(('text', 'change1', 'change2', 'expected'), [
        ('line1\nline2\n', [4, [1, '0'], 7], [10, [1, '1'], 1], 'line0\nline1\n'),
        ('line1\nline2\n', [5, [0, '', ''], 7], [7, [3], 2], 'line1\n\nl2\n'),
        ('line1\nline2\n', [5, [7]], [9, [0, 'e'], 3], 'line1e'),
        ('ABCDE', [1, [1], 3], [3, [1], 1], 'ACE'),
        ('AD', [1, [0, 'B'], 1], [1, [0, 'C'], 1], 'ABCD'),
        ('AD', [1, [0, ' 🤦🏼‍♂️ '], 1], [1, [0, 'C'], 1], 'A 🤦🏼‍♂️ CD'),
    ])
    def test_operational_transform(self, text, change1, change2, expected):
        c1 = ChangeSet.from_dict(change1)
        c2 = ChangeSet.from_dict(change2)
        assert c1.compose(c2.map(c1)).apply(text) == expected
        assert c2.compose(c1.map(c2, True)).apply(text) == expected

        text1 = c1.apply(text)
        updates, _ = rebase_updates(updates=[Update(client_id='c2', version=2, changes=c2)], selection=None, over=[Update(client_id='c1', version=1, changes=c1)])
        assert len(updates) == 1
        assert updates[0].changes.apply(text1) == expected

        # Rebase already applied changes
        assert rebase_updates(updates=[Update(client_id='c2', version=2, changes=c2)], selection=None, over=[Update(client_id='c1', version=1, changes=c1), Update(client_id='c2', version=2, changes=c2)])[0] == []

    @pytest.mark.parametrize(('selection', 'change', 'expected'), [
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
        ([{'anchor': 10, 'head': 20}], [5, [20], [0, 'replaced whole range'], 20], [{'anchor': 5, 'head': 5}]),
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

    @pytest.mark.parametrize(('text_before', 'text_after'), [
        ('line1\nline2\n', 'line1\nline2\n'),  # same text
        ('', 'new text'),
        ('old text', ''),
        ('old text\nline2', 'completely replaced\nwith new content'),
        ('line1\nline2\n', 'line1\ninserted\nline2\n'),
        ('line1\ndeleted\nline2', 'line1\nline2\n'),
        ('line1\nsome characters changed\nline2\n', 'line1\nsome char___ers changed\nline2\n'),
        # newline handling
        ('line1\nline2\n', 'line1\nchanged\n'),
        ('line1\nline2', 'line1\nchanged'),
        ('line1\nline2', 'line1\nchanged\n'),
        ('line1\nline2\n', 'line1\nchanged'),
        ('line1\nline2\n', 'line1\n\n\nchanged\n'),
        # unicode handling
        ('line1\nline2\n', 'line1 🤦🏼‍♂️ text\nline2\n'),
        ('line1 🤦🏼‍♂️ text\nline2\n', 'line1 🤦🏼‍♂️ text\nline2\nline 3 🤦🏼‍♂️'),
        ('line1 🤦🏼‍♂️ text\nline2\n', 'line1 text\nline2\n'),
        ('line1 text\nline2\n', 'line1 🤦🏼‍♂️\nline2\n'),
        ('line1 🤦🏼‍♂️\nline2\n', 'line1 🤷\nline2\n'),
        ('line1 🤦🏼‍♂️\nline2\n', 'line1 🤦🏿‍♀️\nline2\n'),
        # multiple changes
        ('some example text', 's__e ex__ple t__t'),
        ('some example text', 's_e new example'),
        ('some example text', 's_e text new'),
    ])
    def test_diff_to_changeset(self, text_before, text_after):
        # Forward change
        c1 = ChangeSet.from_diff(text_before, text_after)
        assert c1.apply(text_before) == text_after
        c1.to_dict()

        # Reverse change
        c2 = ChangeSet.from_diff(text_after, text_before)
        assert c2.apply(text_after) == text_before
        c2.to_dict()


@sync_to_async
def create_session(user):
    engine = import_string(settings.SESSION_ENGINE)
    session = engine.SessionStore()
    if user and not user.is_anonymous:
        session[SESSION_KEY] = str(user.id)
        session[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
        session[HASH_SESSION_KEY] = user.get_session_auth_hash()
        session['admin_permissions_enabled'] = True
    session.save()
    return session


@contextlib.asynccontextmanager
async def ws_connect(path, user, consume_init=True, other_clients=None):
    session = await create_session(user)
    consumer = WebsocketCommunicator(
        application=application,
        path=path,
        headers=[(b'cookie', f'{settings.SESSION_COOKIE_NAME}={session.session_key}'.encode())],
    )
    consumer.session = session

    try:
        # Connect
        connected, _ = await consumer.connect()
        assert connected

        if consume_init:
            # Consume initial message
            init = await consumer.receive_json_from()
            assert init.get('type') == CollabEventType.INIT
            consumer.init = init
            consumer.client_id = init['client_id']

            # Consume collab.connect message
            connect = await consumer.receive_json_from()
            assert connect.get('type') == CollabEventType.CONNECT
            assert connect.get('client_id') == init['client_id']

            for c in (other_clients or []):
                msg_connect = await c.receive_json_from()
                assert msg_connect.get('type') == CollabEventType.CONNECT
                assert msg_connect.get('client_id') == init['client_id']

        yield consumer
    finally:
        await consumer.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio()
class TestCollaborativeTextEditing:
    @pytest_asyncio.fixture(autouse=True)
    async def setUp(self):
        def setup_db():
            self.user1 = create_user()
            self.user2 = create_user()
            self.project = create_project(
                members=[self.user1, self.user2],
                findings_kwargs=[{'data': {'field_markdown': 'AB', 'field_list': ['A', 'B']}}],
                comments=False,
            )
            self.finding = self.project.findings.all()[0]
            with collab_context(prevent_events=True):
                self.comment = create_comment(finding=self.finding, path='data.field_markdown', text_range=SelectionRange(anchor=1, head=2))
        await sync_to_async(setup_db)()

        async with ws_connect(path=f'/api/ws/pentestprojects/{self.project.id}/reporting/', user=self.user1) as self.client1, \
                   ws_connect(path=f'/api/ws/pentestprojects/{self.project.id}/reporting/', user=self.user2, other_clients=[self.client1]) as self.client2:
            yield

    async def refresh_data(self):
        self.finding = await PentestFinding.objects \
            .select_related('project__project_type') \
            .aget(id=self.finding.id)
        await self.comment.arefresh_from_db()

    async def assert_event_received(self, event):
        res1 = await self.client1.receive_json_from()
        res2 = await self.client2.receive_json_from()
        self.assert_events_equal(res1, event)
        self.assert_events_equal(res2, event)
        return res1

    def assert_events_equal(self, actual, expected):
        for k, v in expected.items():
            assert actual[k] == v

    async def test_concurrent_updates(self):
        # Concurrent updates of same version
        event_base = {'type': CollabEventType.UPDATE_TEXT, 'path': f'findings.{self.finding.finding_id}.data.field_markdown'}
        await self.client1.send_json_to(event_base | {'updates': [{'changes': [1, [0, '1'], 1]}], 'selection': {'main': 0, 'ranges': [{'anchor': 2, 'head': 2}]}, 'version': self.client1.init['version']})
        await self.client2.send_json_to(event_base | {'updates': [{'changes': [1, [0, '2'], 1]}], 'selection': {'main': 0, 'ranges': [{'anchor': 2, 'head': 2}]}, 'version': self.client1.init['version']})

        await self.assert_event_received(event_base | {
            'updates': [{'changes': [1, [0, '1'], 1]}],
            'selection': {'main': 0, 'ranges': [{'anchor': 2, 'head': 2}]},
            'comments': [{'id': str(self.comment.id), 'path': f'findings.{self.finding.finding_id}.data.field_markdown', 'text_range': {'from': 2, 'to': 3}}],
        })
        res2 = await self.assert_event_received(event_base | {
            'updates': [{'changes': [2, [0, '2'], 1]}],
            'selection': {'main': 0, 'ranges': [{'anchor': 3, 'head': 3}]},
            'comments': [{'id': str(self.comment.id), 'path': f'findings.{self.finding.finding_id}.data.field_markdown', 'text_range': {'from': 3, 'to': 4}}],
        })
        version = res2['version']
        assert version > self.client1.init['version']

        await self.refresh_data()
        assert self.finding.data['field_markdown'] == 'A12B'
        assert self.comment.text_range == SelectionRange(anchor=3, head=4)

        # Third update after both previous changes (using updated version)
        event3 = event_base | {'updates': [{'changes': [4, [0, '3']]}], 'selection': {'main': 0, 'ranges': [{'anchor': 5, 'head': 5}]}}
        await self.client1.send_json_to(event3 | {'version': version})
        await self.assert_event_received(event3 | {
            'comments': [{'id': str(self.comment.id), 'path': f'findings.{self.finding.finding_id}.data.field_markdown', 'text_range': {'from': 3, 'to': 4}}],
        })

        await self.refresh_data()
        assert self.finding.data['field_markdown'] == 'A12B3'
        assert self.comment.text_range == SelectionRange(anchor=3, head=4)

    async def test_concurrent_updates_awareness(self):
        event_base = {'path': f'findings.{self.finding.finding_id}.data.field_markdown', 'version': self.client1.init['version']}
        await self.client1.send_json_to(event_base | {'type': CollabEventType.UPDATE_TEXT, 'updates': [{'changes': [1, [0, '1'], 1]}]})
        await self.client2.send_json_to(event_base | {'type': CollabEventType.AWARENESS, 'selection': {'main': 0, 'ranges': [{'anchor': 0, 'head': 2}]}})

        await self.assert_event_received({'type': CollabEventType.UPDATE_TEXT})
        await self.assert_event_received({'type': CollabEventType.AWARENESS, 'selection': {'main': 0, 'ranges': [{'anchor': 0, 'head': 3}]}})

    async def test_rebase_updates(self):
        event_base = {'type': CollabEventType.UPDATE_TEXT, 'path': f'findings.{self.finding.finding_id}.data.field_markdown', 'version': self.client1.init['version']}
        updates = [{'changes': [1, [0, '1'], 1]}, {'changes': [2, [0, '2'], 1]}, {'changes': [3, [0, '3'], 1]}, {'changes': [4, [0, '4'], 1]}]
        await self.client1.send_json_to(event_base | {'updates': updates[:2], 'selection': {'main': 0, 'ranges': [{'anchor': 3, 'head': 3}]}})
        await self.client1.send_json_to(event_base | {'updates': updates, 'selection': {'main': 0, 'ranges': [{'anchor': 5, 'head': 5}]}})

        res1 = await self.client1.receive_json_from()
        assert res1['updates'] == updates[:2]
        assert res1['selection'] == {'main': 0, 'ranges': [{'anchor': 3, 'head': 3}]}
        res2 = await self.client1.receive_json_from()
        assert res2['updates'] == updates[2:]
        assert res2['selection'] == {'main': 0, 'ranges': [{'anchor': 5, 'head': 5}]}

        await self.refresh_data()
        assert self.finding.data['field_markdown'] == 'A1234B'

    async def test_concurrent_list_updates(self):
        # Concurrent add list items
        event_base_create = {'type': CollabEventType.CREATE, 'path': f'findings.{self.finding.finding_id}.data.field_list', 'version': self.client1.init['version']}
        await self.client1.send_json_to(event_base_create | {'value': 'C'})
        await self.client2.send_json_to(event_base_create | {'value': 'D'})

        await self.assert_event_received({'type': CollabEventType.CREATE, 'path': f'findings.{self.finding.finding_id}.data.field_list.[2]', 'value': 'C'})
        res2 = await self.assert_event_received({'type': CollabEventType.CREATE, 'path': f'findings.{self.finding.finding_id}.data.field_list.[3]', 'value': 'D'})

        await self.refresh_data()
        assert self.finding.data['field_list'] == ['A', 'B', 'C', 'D']

        # Add comments
        with collab_context(prevent_events=True):
            comment_list_a = await sync_to_async(create_comment)(finding=self.finding, path='data.field_list.[0]')
            comment_list_c = await sync_to_async(create_comment)(finding=self.finding, path='data.field_list.[2]')

        # Delete list item
        event_delete = {'type': CollabEventType.DELETE, 'path': f'findings.{self.finding.finding_id}.data.field_list.[2]'}
        await self.client1.send_json_to(event_delete | {'version': res2['version']})
        res3 = await self.assert_event_received(event_delete | {'comments': [{'id': str(comment_list_c.id), 'path': None}]})

        await self.refresh_data()
        assert self.finding.data['field_list'] == ['A', 'B', 'D']

        # Sort list
        event_update_key = {'type': CollabEventType.UPDATE_KEY, 'path': f'findings.{self.finding.finding_id}.data.field_list', 'value': ['B', 'D', 'A']}
        await self.client1.send_json_to(event_update_key | {'version': res3['version'], 'sort': [{'id': 0, 'order': 2}, {'id': 1, 'order': 0}, {'id': 2, 'order': 1}]})
        await self.assert_event_received(event_update_key | {'comments': [{'id': str(comment_list_a.id), 'path': f'findings.{self.finding.finding_id}.data.field_list.[2]', 'text_range': None}]})

        await self.refresh_data()
        await comment_list_a.arefresh_from_db()
        assert self.finding.data['field_list'] == ['B', 'D', 'A']
        assert comment_list_a.path == 'data.field_list.[2]'

    async def test_client_collab_info_lifecycle(self):
        async with ws_connect(path=f'/api/ws/pentestprojects/{self.project.id}/reporting/', user=self.user1, consume_init=False) as client:
            # path of other clients in collab.init
            init = await client.receive_json_from()
            await client.receive_json_from()
            init_client_infos = [c async for c in CollabClientInfo.objects.filter(client_id__in=[init['client_id'], self.client1.client_id, self.client2.client_id])]
            assert [copy_keys(c, ['client_id', 'path']) for c in init['clients']] == \
                   [copy_keys(c, ['client_id', 'path']) for c in init_client_infos]

            # client info created on connect
            client_info = await CollabClientInfo.objects.select_related('user').aget(client_id=init['client_id'])
            assert client_info.user == self.user1
            assert client_info.path is None

            # path updated on collab.awareness
            await client.send_json_to({'type': CollabEventType.AWARENESS, 'path': f'findings.{self.finding.finding_id}.data.field_string', 'version': init['version']})
            await client.receive_json_from()
            await client_info.arefresh_from_db()
            assert client_info.path == f'findings.{self.finding.finding_id}.data.field_string'

            # path updated on collab.update_text
            await client.send_json_to({'type': CollabEventType.UPDATE_TEXT, 'path': f'findings.{self.finding.finding_id}.data.field_markdown', 'version': init['version'], 'updates': [{'changes': [1, [0, '1'], 1]}]})
            await client.receive_json_from()
            await client_info.arefresh_from_db()
            assert client_info.path == f'findings.{self.finding.finding_id}.data.field_markdown'

        # deleted on disconnect
        assert not await CollabClientInfo.objects.filter(client_id=init['client_id']).aexists()

    async def test_http_fallback(self):
        self.client_http = api_client(self.user1)
        res1 = await sync_to_async(self.client_http.get)(reverse('projectreporting-fallback', kwargs={'project_pk': self.project.id}))
        assert res1.status_code == 200, res1.data
        assert json.loads(json.dumps(res1.data['data'], cls=DjangoJSONEncoder)) == self.client1.init['data']
        version = res1.data['version']
        assert version == self.client1.init['version']

        event1 = {'type': CollabEventType.UPDATE_TEXT, 'path': f'findings.{self.finding.finding_id}.data.field_markdown', 'updates': [{'changes': [1, [0, '1'], 1]}]}
        await self.client1.send_json_to(event1 | {'version': version})
        await self.assert_event_received(event1)

        event2 = {'type': CollabEventType.UPDATE_TEXT, 'path': f'findings.{self.finding.finding_id}.data.field_markdown', 'updates': [{'changes': [1, [0, '2'], 1]}]}
        event3 = {'type': CollabEventType.UPDATE_KEY, 'path': f'findings.{self.finding.finding_id}.data.field_list', 'value': ['N', 'E', 'W']}
        res2 = await sync_to_async(self.client_http.post)(
            path=reverse('projectreporting-fallback', kwargs={'project_pk': self.project.id}),
            data={'version': version, 'client_id': res1.data['client_id'], 'messages': [event2 | {'version': version}, event3 | {'version': version}]},
        )
        assert res2.status_code == 200, res2.data
        assert res2.data['version'] > version
        assert len(res2.data['messages']) == 3
        event2['updates'] = [{'changes': [2, [0, '2'], 1]}]
        self.assert_events_equal(res2.data['messages'][0], event1 | {'client_id': self.client1.client_id})
        self.assert_events_equal(res2.data['messages'][1], event2 | {'client_id': res1.data['client_id']})
        self.assert_events_equal(res2.data['messages'][2], event3 | {'client_id': res1.data['client_id']})
        await self.assert_event_received(event2)
        await self.assert_event_received(event3)

        await self.refresh_data()
        assert self.finding.data['field_markdown'] == 'A12B'
        assert self.finding.data['field_list'] == event3['value']

        res2 = await sync_to_async(self.client_http.post)(
            path=reverse('projectreporting-fallback', kwargs={'project_pk': self.project.id}),
            data={'version': res2.data['version'], 'client_id': res1.data['client_id'], 'messages': []},
        )
        assert res2.status_code == 200, res2.data
        assert len(res2.data['messages']) == 0


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio()
class TestProjectNotesDbSync:
    @pytest_asyncio.fixture(autouse=True)
    async def setUp(self):
        def setup_db():
            self.user1 = create_user()
            self.user2 = create_user()
            self.project = create_project(members=[self.user1, self.user2], notes_kwargs=[{'checked': None, 'icon_emoji': None, 'title': 'ABC', 'text': 'ABC'}])
            self.note = self.project.notes.all()[0]
            self.note_path_prefix = f'notes.{self.note.note_id}'
            self.api_client1 = api_client(self.user1)
        await sync_to_async(setup_db)()

        async with ws_connect(path=f'/api/ws/pentestprojects/{self.project.id}/notes/', user=self.user1) as self.client1, \
                   ws_connect(path=f'/api/ws/pentestprojects/{self.project.id}/notes/', user=self.user2, other_clients=[self.client1]) as self.client2:
            yield

    async def refresh_data(self):
        await self.note.arefresh_from_db()

    async def assert_event(self, event):
        res1 = await self.client1.receive_json_from()
        res2 = await self.client2.receive_json_from()
        for k, v in event.items():
            assert res1[k] == res2[k] == v

    async def test_update_key(self):
        event = {'type': CollabEventType.UPDATE_KEY, 'path': self.note_path_prefix + '.icon_emoji', 'value': '👍'}
        await self.client1.send_json_to(event)

        # Websocket messages sent to clients
        await self.assert_event(event | {'client_id': self.client1.client_id})

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
        await self.assert_event(event | {'client_id': self.client1.client_id})

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
        await self.assert_event({'type': CollabEventType.CREATE, 'path': f'notes.{res_api.data["id"]}', 'value': res_api.data, 'client_id': None})
        # Sort event
        await self.assert_event({'type': CollabEventType.SORT, 'path': 'notes', 'client_id': None})

    async def test_delete_sync(self):
        await self.note.adelete()
        await self.assert_event({'type': CollabEventType.DELETE, 'path': self.note_path_prefix, 'client_id': None})

    async def test_update_key_sync(self):
        await sync_to_async(self.api_client1.patch)(
            path=reverse('projectnotebookpage-detail', kwargs={'project_pk': self.project.id, 'id': self.note.note_id}),
            data={'checked': True, 'title': 'updated', 'text': 'ABCDEF'})

        r1_1 = await self.client1.receive_json_from()
        r1_2 = await self.client1.receive_json_from()
        r1_3 = await self.client1.receive_json_from()
        res1 = {r1_1['path']: r1_1, r1_2['path']: r1_2, r1_3['path']: r1_3}

        r2_1 = await self.client2.receive_json_from()
        r2_2 = await self.client2.receive_json_from()
        r2_3 = await self.client2.receive_json_from()
        res2 = {r2_1['path']: r2_1, r2_2['path']: r2_2, r2_3['path']: r2_3}

        for k, v in ({'type': CollabEventType.UPDATE_KEY, 'path': self.note_path_prefix + '.checked', 'value': True, 'client_id': None}).items():
            assert res1[self.note_path_prefix + '.checked'][k] == res2[self.note_path_prefix + '.checked'][k] == v
        for k, v in ({'type': CollabEventType.UPDATE_TEXT, 'path': self.note_path_prefix + '.title', 'updates': [{'changes': [[3, 'updated']]}], 'client_id': None}).items():
            assert res1[self.note_path_prefix + '.title'][k] == res2[self.note_path_prefix + '.title'][k] == v
        for k, v in ({'type': CollabEventType.UPDATE_TEXT, 'path': self.note_path_prefix + '.text', 'updates': [{'changes': [3, [0, 'DEF']]}], 'client_id': None}).items():
            assert res1[self.note_path_prefix + '.text'][k] == res2[self.note_path_prefix + '.text'][k] == v

    async def test_sort_sync(self):
        res = await sync_to_async(self.api_client1.post)(
            path=reverse('projectnotebookpage-sort', kwargs={'project_pk': self.project.id}),
            data=[{'id': self.note.note_id, 'order': 1, 'parent': None}])
        await self.assert_event({'type': CollabEventType.SORT, 'path': 'notes', 'client_id': None, 'sort': res.data})

    async def test_import_sync(self):
        def import_notes():
            res = self.api_client1.post(
                path=reverse('projectnotebookpage-import', kwargs={'project_pk': self.project.id}),
                data={'file': ContentFile(content=b''.join(export_notes(self.project)), name='export.tar.gz')},
                format='multipart',
            )
            return res.data
        notes_imported = await sync_to_async(import_notes)()

        for n in notes_imported:
            await self.assert_event({'type': CollabEventType.CREATE, 'path': f'notes.{n["id"]}', 'value': n, 'client_id': None})
        await self.assert_event({'type': CollabEventType.SORT, 'path': 'notes', 'client_id': None})

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

    async def test_logout_write(self):
        await sync_to_async(self.client1.session.flush)()

        await self.client1.send_json_to({'type': CollabEventType.UPDATE_KEY, 'path': self.note_path_prefix + '.checked', 'value': True})
        res = await self.client1.receive_output()
        assert res['type'] == 'websocket.close'

    async def test_logout_read(self):
        await sync_to_async(self.client1.session.flush)()

        with mock_time(after=timedelta(minutes=2)):
            await self.client2.send_json_to({'type': CollabEventType.UPDATE_KEY, 'path': self.note_path_prefix + '.checked', 'value': True})
            await self.client2.receive_json_from()

            res1 = await self.client1.receive_output()
            assert res1['type'] == 'websocket.close'


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio()
class TestProjectReportingDbSync:
    @pytest_asyncio.fixture(autouse=True)
    async def setUp(self):
        def setup_db():
            self.user1 = create_user()
            self.user2 = create_user()
            self.project_type = create_project_type()
            initial_data = {
                'field_int': 1,
                'field_user': None,
                'field_string': 'ABC',
                'field_markdown': 'ABC',
                'field_list': ['ABC'],
                'field_list_objects': [{'field_int': 1, 'field_string': 'ABC'}],
            }
            self.project = create_project(
                project_type=self.project_type,
                members=[self.user1, self.user2],
                report_data=ensure_defined_structure(value=initial_data, definition=self.project_type.all_report_fields_obj),
                findings_kwargs=[{'data': ensure_defined_structure(value=initial_data, definition=self.project_type.finding_fields_obj)}],
            )
            self.section = self.project.sections.get(section_id='other')
            self.section_path_prefix = f'sections.{self.section.section_id}'
            self.finding = self.project.findings.all()[0]
            self.finding_path_prefix = f'findings.{self.finding.finding_id}'

            create_comment(section=self.section, path='data.field_markdown', text_range=SelectionRange(anchor=1, head=2))
            create_comment(finding=self.finding, path='data.field_markdown', text_range=SelectionRange(anchor=1, head=2))

            self.api_client1 = api_client(self.user1)
        await sync_to_async(setup_db)()

        async with ws_connect(path=f'/api/ws/pentestprojects/{self.project.id}/reporting/', user=self.user1) as self.client1, \
                   ws_connect(path=f'/api/ws/pentestprojects/{self.project.id}/reporting/', user=self.user2, other_clients=[self.client1]) as self.client2:
            yield

    async def assert_event(self, event):
        res1 = await self.client1.receive_json_from()
        res2 = await self.client2.receive_json_from()
        for k, v in event.items():
            assert res1[k] == res2[k] == v

    async def refresh_data(self, obj=None):
        self.section = await ReportSection.objects \
            .select_related('assignee', 'project__project_type') \
            .aget(id=self.section.id)
        self.finding = await PentestFinding.objects \
            .select_related('assignee', 'project__project_type') \
            .aget(id=self.finding.id)

        obj_id = getattr(obj, 'id', None)
        return self.section if obj_id == self.section.id else \
               self.finding if obj_id == self.finding.id else \
               None

    @pytest.mark.parametrize(('obj_type', 'path', 'value'), [(a,) + b for a, b in itertools.product(['finding', 'section'], [
        ('status', ReviewStatus.FINISHED),
        ('data.field_int', 1337),
        ('data.field_user', lambda s: str(s.user1.id)),
        ('data.field_object.field_int', 1337),
        ('data.field_list_objects.[0].field_int', 1337),
        ('data.field_list', ['a', 'b', 'c']),
    ])])
    async def test_update_key(self, obj_type, path, value):
        if obj_type == 'section':
            obj = self.section
            path_prefix = self.section_path_prefix
        elif obj_type == 'finding':
            obj = self.finding
            path_prefix = self.finding_path_prefix

        if callable(value):
            value = value(self)
        event = {'type': CollabEventType.UPDATE_KEY, 'path': path_prefix + '.' + path, 'value': value}
        await self.client1.send_json_to(event)

        # Websocket messages sent to clients
        await self.assert_event(event | {'client_id': self.client1.client_id})

        # Changes synced to DB
        obj = await self.refresh_data(obj)
        path_parts = path.split('.')
        value_db = getattr(obj, path_parts[0]) if len(path_parts) == 1 else get_value_at_path(obj.data, path_parts[1:])
        assert value_db == value

        # History entry created
        assert await obj.history.acount() == 2
        obj_h = await obj.history.order_by('-history_date').afirst()
        assert obj_h.history_type == '~'
        value_h = getattr(obj_h, path_parts[0]) if len(path_parts) == 1 else get_value_at_path(obj_h.custom_fields, path_parts[1:])
        assert value_h == value_db

    @pytest.mark.parametrize(('obj_type', 'path'), list(itertools.product(['finding', 'section'], [
        'data.field_string',
        'data.field_markdown',
        'data.field_list.[0]',
        'data.field_list_objects.[0].field_string',
    ])))
    async def test_update_text(self, obj_type, path):
        if obj_type == 'section':
            obj = self.section
            path_prefix = self.section_path_prefix
        elif obj_type == 'finding':
            obj = self.finding
            path_prefix = self.finding_path_prefix

        event = {'type': CollabEventType.UPDATE_TEXT, 'path': path_prefix + '.' + path, 'updates': [{'changes': [3, [0, 'D']]}]}
        await self.client1.send_json_to(event | {'version': self.client1.init['version']})

        # Websocket messages sent to clients
        await self.assert_event(event | {'client_id': self.client1.client_id})

        # Changes synced to DB
        obj = await self.refresh_data(obj)
        value_db = get_value_at_path(obj.data, path.split('.')[1:])
        assert value_db == 'ABCD'

        # History entry created
        assert await obj.history.acount() == 2
        obj_h = await obj.history.order_by('-history_date').afirst()
        assert obj_h.history_type == '~'
        value_h = get_value_at_path(obj_h.custom_fields, path.split('.')[1:])
        assert value_h == value_db

    @pytest.mark.parametrize(('obj_type', 'changes', 'expected_text_range'), [(a,) + b for a, b in itertools.product(['finding', 'section'], [
        ([0, [0, 'before'], 3], SelectionRange(anchor=7, head=8)),
        ([3, [0, 'after']], SelectionRange(anchor=1, head=2)),
        ([1, [1, 'inside'], 1], SelectionRange(anchor=1, head=7)),
        ([0, [3]], None),
        ([0, [3], [0, 'replaced']], None),
    ])])
    async def test_update_text_comment_text_range(self, obj_type, changes, expected_text_range):
        if obj_type == 'section':
            obj = self.section
            path_prefix = self.section_path_prefix
        elif obj_type == 'finding':
            obj = self.finding
            path_prefix = self.finding_path_prefix

        event = {'type': CollabEventType.UPDATE_TEXT, 'path': path_prefix + '.data.field_markdown', 'updates': [{'changes': changes}]}
        await self.client1.send_json_to(event | {'version': self.client1.init['version']})

        # Websocket messages sent to clients
        comment = await obj.comments.afirst()
        await self.assert_event(event | {
            'client_id': self.client1.client_id,
            'comments': [{'id': str(comment.id), 'path': path_prefix + '.data.field_markdown', 'text_range': {'from': expected_text_range.from_, 'to': expected_text_range.to} if expected_text_range else None}],
        })

        # Changes synced to DB
        await comment.arefresh_from_db()
        assert comment.text_range == expected_text_range

    async def test_create_finding_sync(self):
        res_api = await sync_to_async(self.api_client1.post)(
            path=reverse('finding-list', kwargs={'project_pk': self.project.id}),
            data={'data': {'title': 'new finding'}})
        api_data = json.loads(json.dumps(res_api.data, cls=DjangoJSONEncoder))
        # Create event
        await self.assert_event({'type': CollabEventType.CREATE, 'path': f'findings.{res_api.data["id"]}', 'value': api_data, 'client_id': None})

    async def test_delete_finding_sync(self):
        await self.finding.adelete()
        await self.assert_event({'type': CollabEventType.DELETE, 'path': self.finding_path_prefix, 'client_id': None})

    @pytest.mark.parametrize(('obj_type', 'path', 'value'), [(a,) + b for a, b in itertools.product(['finding', 'section'], [
        ('status', ReviewStatus.FINISHED),
        ('data.field_int', 1337),
        ('data.field_object.field_int', 1337),
        ('data.field_list_objects.[0].field_int', 1337),
        ('data.field_list', []),
        ('data.field_list', ['A', 'B', 'C']),
    ])])
    async def test_update_key_sync(self, obj_type, path, value):
        if obj_type == 'section':
            obj = self.section
            path_prefix = self.section_path_prefix
        elif obj_type == 'finding':
            obj = self.finding
            path_prefix = self.finding_path_prefix

        if path.startswith('data'):
            updated_data = obj.data
            set_value_at_path(updated_data, path.split('.')[1:], value)
            obj.update_data(updated_data)
        else:
            setattr(obj, path, value)
        await obj.asave()

        # Websocket messages sent to clients
        await self.assert_event({'type': CollabEventType.UPDATE_KEY, 'path': f'{path_prefix}.{path}', 'value': value, 'client_id': None})
        assert await self.client1.receive_nothing()

    @pytest.mark.parametrize(('obj_type', 'path'), list(itertools.product(['finding', 'section'], [
        'data.field_string',
        'data.field_markdown',
        'data.field_list.[0]',
        'data.field_list_objects.[0].field_string',
    ])))
    async def test_update_text_sync(self, obj_type, path):
        if obj_type == 'section':
            obj = self.section
            path_prefix = self.section_path_prefix
        elif obj_type == 'finding':
            obj = self.finding
            path_prefix = self.finding_path_prefix

        updated_data = obj.data
        set_value_at_path(updated_data, path.split('.')[1:], 'ABCDEF')
        obj.update_data(updated_data)
        await obj.asave()

        # Websocket messages sent to clients
        await self.assert_event({'type': CollabEventType.UPDATE_TEXT, 'path': f'{path_prefix}.{path}', 'updates': [{'changes': [3, [0, 'DEF']]}], 'client_id': None})
        assert await self.client1.receive_nothing()

    async def test_sort_findings_sync(self):
        res = await sync_to_async(self.api_client1.post)(
            path=reverse('finding-sort', kwargs={'project_pk': self.project.id}),
            data=[{'id': self.finding.finding_id, 'order': 1, 'parent': None}])
        await self.assert_event({'type': CollabEventType.SORT, 'path': 'findings', 'client_id': None, 'sort': res.data})

    async def test_update_project_sync(self):
        self.project.override_finding_order = True
        await self.project.asave()
        await self.assert_event({'type': CollabEventType.UPDATE_KEY, 'path': 'project.override_finding_order', 'value': True, 'client_id': None})

        project_type = await sync_to_async(create_project_type)()
        self.project.project_type = project_type
        await self.project.asave()
        event_project_type_changed = {'type': CollabEventType.UPDATE_KEY, 'path': 'project.project_type', 'value': str(project_type.id), 'client_id': None}
        await self.assert_event(event_project_type_changed)

        project_type.report_sections = copy.deepcopy(project_type.report_sections)
        next(s for s in project_type.report_sections if s['id'] == 'other')['fields'].append({'id': 'new_field', 'type': 'string'})
        await project_type.asave()
        await self.assert_event(event_project_type_changed)

        project_type.finding_fields += [{'id': 'new_field', 'type': 'string'}]
        await project_type.asave()
        await self.assert_event(event_project_type_changed)

    async def test_comment_sync(self):
        # Create comment
        res1 = await sync_to_async(self.api_client1.post)(
            path=reverse('comment-list', kwargs={'project_pk': self.project.id}),
            data={'path': f'{self.finding_path_prefix}.data.field_markdown', 'text_range': {'from': 1, 'to': 2}, 'text': 'comment text'},
        )
        await self.assert_event({ 'type': CollabEventType.CREATE, 'path': f'comments.{res1.data["id"]}', 'value': res1.data, 'client_id': None })

        # # Update comment
        comment_url = reverse('comment-detail', kwargs={'project_pk': self.project.id, 'pk': res1.data['id']})
        comment_path_prefix = f'comments.{res1.data["id"]}'
        res2 = await sync_to_async(self.api_client1.patch)(comment_url, data={'text': 'updated'})
        await self.assert_event({ 'type': CollabEventType.UPDATE_KEY, 'path': comment_path_prefix + '.text', 'value': res2.data['text'], 'client_id': None })

        # Create answer
        res3 = await sync_to_async(self.api_client1.post)(
            path=reverse('commentanswer-list', kwargs={'project_pk': self.project.id, 'comment_pk': res1.data['id']}),
            data={'text': 'answer text'},
        )
        await self.assert_event({ 'type': CollabEventType.UPDATE_KEY, 'path': comment_path_prefix + '.answers', 'value': [res3.data], 'client_id': None })

        # Update answer
        answer_url = reverse('commentanswer-detail', kwargs={'project_pk': self.project.id, 'comment_pk': res1.data['id'], 'pk': res3.data['id']})
        res4 = await sync_to_async(self.api_client1.patch)(answer_url, data={'text': 'updated'})
        await self.assert_event({ 'type': CollabEventType.UPDATE_KEY, 'path': comment_path_prefix + '.answers', 'value': [res4.data], 'client_id': None})

        # Delete comment
        await sync_to_async(self.api_client1.delete)(comment_url)
        await self.assert_event({ 'type': CollabEventType.DELETE, 'path': comment_path_prefix, 'client_id': None })

    async def test_comment_create_text_range_rebase(self):
        version = self.client1.init['version']
        event_update = {'type': CollabEventType.UPDATE_TEXT, 'path': f'{self.finding_path_prefix}.data.field_markdown', 'updates': [{'changes': [0, [0, 'before'], 2, [0, 'inside'], 1, [0, 'after']]}]}
        await self.client1.send_json_to(event_update | {'version': version})
        await self.assert_event(event_update)

        res = await sync_to_async(self.api_client1.post)(
            path=reverse('comment-list', kwargs={'project_pk': self.project.id}) + f'?version={version}',
            data={'path': f'{self.finding_path_prefix}.data.field_markdown', 'text_range': {'from': 1, 'to': 3}, 'text': 'comment text'},
        )
        assert res.data['text_range'] == {'from': 7, 'to': 15}
        assert res.data['text_original'] == 'BinsideC'
        await self.assert_event({'type': CollabEventType.CREATE, 'path': f'comments.{res.data["id"]}', 'value': res.data, 'client_id': None})



@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio()
class TestSharedProjectNotesDbSync:
    @pytest_asyncio.fixture(autouse=True)
    async def setUp(self):
        def setup_db():
            self.user = create_user()
            self.project = create_project(members=[self.user], notes_kwargs=[])
            note_kwargs = {'checked': None, 'icon_emoji': None, 'title': 'ABC', 'text': 'ABC'}
            self.note_shared = create_projectnotebookpage(project=self.project, **note_kwargs)
            self.childnote_shared = create_projectnotebookpage(project=self.project, parent=self.note_shared, **note_kwargs)
            self.note_not_shared = create_projectnotebookpage(project=self.project, **note_kwargs)
            self.childnote_not_shared = create_projectnotebookpage(project=self.project, parent=self.note_not_shared, **note_kwargs)
            self.share_info = create_shareinfo(note=self.note_shared)
            self.childnote_shared_path_prefix = f'notes.{self.childnote_shared.note_id}'

            self.api_client_public = api_client()
            self.api_client_user = api_client(self.user)
        await sync_to_async(setup_db)()

        async with ws_connect(path=f'/api/ws/pentestprojects/{self.project.id}/notes/', user=self.user) as self.client_user, \
                   ws_connect(path=f'/api/public/ws/shareinfos/{self.share_info.id}/notes/', user=None, other_clients=[self.client_user]) as self.client_public:
            yield

    async def refresh_data(self):
        await self.note_shared.arefresh_from_db()
        await self.childnote_shared.arefresh_from_db()
        await self.note_not_shared.arefresh_from_db()
        await self.childnote_not_shared.arefresh_from_db()

    async def assert_event(self, event, user=True, public=True):
        res_user = None
        res_public = None

        if user is True:
            res_user = await self.client_user.receive_json_from()
        elif user is False:
            assert await self.client_user.receive_nothing()

        if public is True:
            res_public = await self.client_public.receive_json_from()
        elif public is False:
            assert await self.client_public.receive_nothing()

        for k, v in event.items():
            if res_user:
                assert res_user[k] == v
            if res_public:
                assert res_public[k] == v
        return res_public

    async def test_update_key(self):
        # Public event
        event1 = {'type': CollabEventType.UPDATE_KEY, 'path': self.childnote_shared_path_prefix + '.icon_emoji', 'value': '👍'}
        await self.client_public.send_json_to(event1)
        await self.assert_event(event1 | {'client_id': self.client_public.client_id})

        # User event
        event2 = event1 | {'value': '👎'}
        await self.client_user.send_json_to(event2)
        await self.assert_event(event2 | {'client_id': self.client_user.client_id})

        # Changes synced to DB
        await self.refresh_data()
        assert self.childnote_shared.icon_emoji == event2['value']

        # History entry created
        assert await self.childnote_shared.history.acount() == 3
        note_h = await self.childnote_shared.history.order_by('-history_date').afirst()
        assert note_h.history_type == '~'
        assert note_h.icon_emoji == self.childnote_shared.icon_emoji

    async def test_update_text(self):
        # Public event
        event1 = {'type': CollabEventType.UPDATE_TEXT, 'path': self.childnote_shared_path_prefix + '.text', 'updates': [{'changes': [3, [0, 'D']]}]}
        await self.client_public.send_json_to(event1 | {'version': self.client_public.init['version']})
        event1_res = await self.assert_event(event1 | {'client_id': self.client_public.client_id})

        # User event
        event2 = event1 | {'updates': [{'changes': [4, [0, 'E']]}]}
        await self.client_user.send_json_to(event2 | {'version': event1_res['version']})
        await self.assert_event(event2 | {'client_id': self.client_user.client_id})

        # Changes synced to DB
        await self.refresh_data()
        assert self.childnote_shared.text == 'ABCDE'

        # History entry created
        assert await self.childnote_shared.history.acount() == 3
        note_h = await self.childnote_shared.history.order_by('-history_date').afirst()
        assert note_h.history_type == '~'
        assert note_h.text == self.childnote_shared.text

    async def test_create_sync(self):
        res_api = await sync_to_async(self.api_client_public.post)(
            path=reverse('sharednote-list', kwargs={'shareinfo_pk': self.share_info.id}),
            data={'title': 'new', 'text': 'new', 'parent': self.note_shared.note_id})
        # Create event
        await self.assert_event({'type': CollabEventType.CREATE, 'path': f'notes.{res_api.data["id"]}', 'value': res_api.data, 'client_id': None})
        # Sort event
        event_sort = await self.assert_event({'type': CollabEventType.SORT, 'path': 'notes', 'client_id': None})
        assert {s['id'] for s in event_sort['sort']} == {str(self.note_shared.note_id), str(self.childnote_shared.note_id), res_api.data['id']}

    async def test_delete_sync(self):
        await self.childnote_shared.adelete()
        await self.assert_event({'type': CollabEventType.DELETE, 'path': self.childnote_shared_path_prefix, 'client_id': None})

    async def test_receive_only_shared_notes(self):
        shared_note_ids = {str(self.note_shared.note_id), str(self.childnote_shared.note_id)}
        # Only shared notes in init message
        assert set(self.client_public.init['data']['notes'].keys()) == shared_note_ids

        # Does not receive events for non-shared notes
        path_prefix_not_shared = f'notes.{self.note_not_shared.note_id}'
        event_update_key = {'type': CollabEventType.UPDATE_KEY, 'path': f'{path_prefix_not_shared}.icon_emoji', 'value': '👍'}
        await self.client_user.send_json_to(event_update_key)
        await self.assert_event(event_update_key, user=True, public=False)

        event_update_text = {'type': CollabEventType.UPDATE_TEXT, 'path': f'{path_prefix_not_shared}.text', 'updates': [{'changes': [3, [0, 'D']]}]}
        await self.client_user.send_json_to(event_update_text | {'version': self.client_user.init['version']})
        await self.assert_event(event_update_text, user=True, public=False)

        # Not-shared note moved to childnote of shared note
        sort_data = [
            {'id': str(self.childnote_shared.note_id), 'parent': str(self.note_shared.note_id), 'order': 1},
            {'id': str(self.childnote_not_shared.note_id), 'parent': str(self.childnote_shared.note_id), 'order': 1},
            {'id': str(self.note_shared.note_id), 'parent': None, 'order': 1},
            {'id': str(self.note_not_shared.note_id), 'parent': str(self.note_shared.note_id), 'order': 2},
        ]
        await sync_to_async(self.api_client_user.post)(reverse('projectnotebookpage-sort', kwargs={'project_pk': self.project.id}), data=sort_data)
        await self.assert_event({'type': CollabEventType.SORT, 'path': 'notes', 'client_id': None, 'sort': sort_data})

    async def test_cannot_update_nonshared_notes(self):
        await self.client_public.send_json_to({'type': CollabEventType.UPDATE_KEY, 'path': f'notes.{self.note_not_shared.note_id}.icon_emoji', 'value': '👍'})
        res = await self.client_public.receive_json_from()
        assert res['type'] == 'error', res


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio()
class TestConsumerPermissions:
    async def ws_connect(self, path, user):
        session = await create_session(user)
        consumer = WebsocketCommunicator(
            application=application,
            path=path,
            headers=[(b'cookie', f'{settings.SESSION_COOKIE_NAME}={session.session_key}'.encode())] if session else [],
        )
        can_read, _ = await consumer.connect()
        can_write = False
        if can_read:
            await consumer.receive_json_from()  # collab.init
            await consumer.receive_json_from()  # collab.connect

            await consumer.send_json_to({'type': CollabEventType.UPDATE_KEY, 'path': 'test', 'value': 'test'})
            msg = await consumer.receive_output()
            can_write = msg['type'] != 'websocket.close'

        await consumer.disconnect()
        return can_read, can_write

    @pytest.mark.parametrize(('user_name', 'project_name', 'expected_read', 'expected_write'), [
        ('member', 'project', True, True),
        ('admin', 'project', True, True),
        ('guest', 'project', True, False),
        ('unauthorized', 'project', False, False),
        ('anonymous', 'project', False, False),
        ('member', 'readonly', True, False),
        ('admin', 'readonly', True, False),
        ('guest', 'readonly', True, False),
    ])
    async def test_project_permissions(self, user_name, project_name, expected_read, expected_write):
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
            return user, projects[project_name]
        with override_settings(GUEST_USERS_CAN_EDIT_PROJECTS=False):
            user, project = await sync_to_async(setup_db)()
            assert await self.ws_connect(f'/api/ws/pentestprojects/{project.id}/notes/', user) == (expected_read, expected_write)
            assert await self.ws_connect(f'/api/ws/pentestprojects/{project.id}/reporting/', user) == (expected_read, expected_write)

            client = api_client(user)
            res = await sync_to_async(client.get)(reverse('projectnotebookpage-fallback', kwargs={'project_pk': project.id}))
            assert res.status_code == (200 if expected_read else 403)
            client_id = res.data.get('client_id', f'{user.id or "anonymous"}/asdf')
            res = await sync_to_async(client.post)(reverse('projectnotebookpage-fallback', kwargs={'project_pk': project.id}), data={'version': 1, 'client_id': client_id, 'messages': []})
            assert res.status_code == (200 if expected_write else 403)

            res = await sync_to_async(client.get)(reverse('projectreporting-fallback', kwargs={'project_pk': project.id}))
            assert res.status_code == (200 if expected_read else 403)
            client_id = res.data.get('client_id', f'{user.id or "anonymous"}/asdf')
            res = await sync_to_async(client.post)(reverse('projectreporting-fallback', kwargs={'project_pk': project.id}), data={'version': 1, 'client_id': client_id, 'messages': []})
            assert res.status_code == (200 if expected_write else 403)

    @pytest.mark.parametrize(('expected', 'user_name'), [
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
            user = users[user_name]
            if user.is_superuser:
                user.admin_permissions_enabled = True
            return user, user_notes
        user, user_notes = await sync_to_async(setup_db)()
        assert await self.ws_connect(f'/api/ws/pentestusers/{user_notes.id}/notes/', user) == (expected, expected)

        client = api_client(user)
        res = await sync_to_async(client.get)(reverse('usernotebookpage-fallback', kwargs={'pentestuser_pk': user_notes.id}))
        assert res.status_code == (200 if expected else 403), res.data
        client_id = res.data.get('client_id', f'{user.id or "anonymous"}/asdf')
        res = await sync_to_async(client.post)(reverse('usernotebookpage-fallback', kwargs={'pentestuser_pk': user_notes.id}), data={'version': 1, 'client_id': client_id, 'messages': []})
        assert res.status_code == (200 if expected else 403), res.data

    @pytest.mark.parametrize(('share_kwargs', 'expected_read', 'expected_write'), [
        ({'is_revoked': True}, False, False),
        ({'expire_date': (timezone.now() - timedelta(days=1)).date()}, False, False),
        ({'password': 'password'}, False, False),
        ({'permissions_write': False}, True, False),
        ({'permissions_write': True, 'project': {'readonly': True}}, True, False),
        ({'permissions_write': True}, True, True),
    ])
    async def test_shared_notes_permissions(self, share_kwargs, expected_read, expected_write):
        def setup_db():
            project = create_project(**share_kwargs.pop('project', {}))
            return create_shareinfo(note=project.notes.first(), **share_kwargs)
        share_info = await sync_to_async(setup_db)()
        assert await self.ws_connect(f'/api/public/ws/shareinfos/{share_info.id}/notes/', user=None) == (expected_read, expected_write)

        client = api_client()
        res = await sync_to_async(client.get)(reverse('sharednote-fallback', kwargs={'shareinfo_pk': share_info.id}))
        assert res.status_code == (200 if expected_read else 403)
        client_id = res.data.get('client_id', 'anonymous/asdf')
        res = await sync_to_async(client.post)(reverse('sharednote-fallback', kwargs={'shareinfo_pk': share_info.id}), data={'version': 1, 'client_id': client_id, 'messages': []})
        assert res.status_code == (200 if expected_write else 403)

        res = await sync_to_async(client.get)(reverse('sharednote-list', kwargs={'shareinfo_pk': share_info.id}))
        assert res.status_code in ([200] if expected_read else [403, 404])
        res = await sync_to_async(client.patch)(reverse('sharednote-detail', kwargs={'shareinfo_pk': share_info.id, 'id': share_info.note.note_id}), data={})
        assert res.status_code in ([200] if expected_write else [403, 404])
