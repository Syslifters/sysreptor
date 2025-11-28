import contextlib
import json
import re
from datetime import timedelta
from unittest import mock

import pytest
from asgiref.sync import async_to_sync
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from langchain.messages import AIMessage, AIMessageChunk, HumanMessage, ToolCall
from langchain.tools import ToolRuntime
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.outputs.chat_generation import ChatGenerationChunk

from sysreptor.ai.agents import get_agent
from sysreptor.ai.agents.project import (
    ProjectContext,
    create_finding,
    get_finding_data,
    get_note_data,
    get_section_data,
    get_template_data,
    list_templates,
    update_field_value,
    update_markdown_field,
)
from sysreptor.ai.models import ChatThread, LangchainCheckpoint
from sysreptor.ai.tasks import cleanup_old_langchain_checkpoints
from sysreptor.tasks.models import PeriodicTask, PeriodicTaskInfo, periodic_task_registry
from sysreptor.tests.mock import (
    api_client,
    create_project,
    create_template,
    create_user,
    mock_time,
    override_configuration,
)
from sysreptor.utils.fielddefinition.utils import get_value_at_path
from sysreptor.utils.utils import copy_keys, omit_keys


class FakeChatModel(GenericFakeChatModel):
    _current_chat_result = None
    message_log: list[dict] = []

    def bind_tools(self, tools, *args, **kwargs):
        return self.bind(tools=tools, **kwargs)

    def _generate(self, *args, **kwargs):
        out = super()._generate(*args, **kwargs)
        self._current_chat_result = out
        self.message_log.append({
            'messages': args[0],
            'response': out,
        })
        return out

    def _stream(self, messages, stop = None, run_manager = None, **kwargs):
        out = list(super()._stream(messages, stop, run_manager, **kwargs))

        if tool_calls := self._current_chat_result.generations[0].message.tool_calls:
            if out:
                out[-1].message.chunk_position = None
            out.append(ChatGenerationChunk(message=AIMessageChunk(content=[], tool_calls=tool_calls, chunk_position='last')))

        return iter(out)


@contextlib.contextmanager
def mock_llm_response(messages: list|None = None, model = None):
    def init_chat_model(*args, **kwargs):
        if isinstance(model, BaseChatModel):
            return model
        else:
            return (model or FakeChatModel)(messages=iter(messages))

    get_agent.cache_clear()
    with mock.patch("langchain.chat_models.init_chat_model", new=init_chat_model):
        yield


@async_to_sync()
async def parse_sse_events(response):
    events = []
    buffer = ""
    async for chunk in response.streaming_content:
        buffer += chunk.decode('utf-8')
        while '\n' in buffer:
            line, buffer = buffer.split('\n', 1)
            if line.startswith('data: '):
                events.append(json.loads(line[6:]))
    if buffer:
        if buffer.startswith('data: '):
            events.append(json.loads(buffer[6:]))
    return events


def to_tokens(text):
    return re.findall(r'([^\s]+|\s+)', text)


def to_message_chunks(event):
    out = []
    for chunk in to_tokens(event['content'].get('reasoning', '')):
        if chunk:
            out.append(event | {'content': omit_keys(event['content'], ['text', 'reasoning']) | {'reasoning': chunk}})
    for chunk in to_tokens(event['content'].get('text', '')):
        if chunk:
            out.append(event | {'content': omit_keys(event['content'], ['text', 'reasoning']) | {'text': chunk}})
    return out


def assert_events_equal(actual, expected):
    assert len(actual) == len(expected)
    ignore_keys = ['content.id', 'content.timestamp']
    for a, e in zip(actual, expected, strict=True):
        assert omit_keys(a, ignore_keys) == omit_keys(e, ignore_keys)


def yaml_indent(text: str, spaces: int = 4) -> str:
    return '\n'.join((' ' * spaces) + line if (line and idx > 0) else '' for idx, line in enumerate(text.splitlines()))


@pytest.mark.django_db()
class TestProjectAgent:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user()
        self.project = create_project(members=[self.user])
        self.client = api_client(user=self.user)

    def send_message(self, message: str, context: dict = None, thread_id: str = None):
        res = self.client.post(reverse('chatthread-list'), data={
            'id': thread_id,
            'agent': 'project_agent',
            'project': self.project.id,
            'messages': [message],
            'context': context or {},
        })
        assert res.status_code == 200
        return parse_sse_events(res)

    def test_agent_flow(self):
        executive_summary = self.project.sections.get(section_id='executive_summary')
        executive_summary.history.all().delete()

        user_messages = [
            'Hi',
            "Update the executive summary to 'New executive summary'.",
        ]
        llm_messages = [
            AIMessage(content='Hi, how can I assist you with your project?'),
            AIMessage(content='Let me update the section for you.', tool_calls=[
                ToolCall(id='tool_call_1', name='update_field_value', args={'path': 'sections.executive_summary.data.executive_summary', 'value': 'New executive summary'}),
            ]),
            AIMessage(content='The executive summary has been updated successfully. How else can I help you?'),
        ]
        with mock_llm_response(messages=llm_messages):
            events = self.send_message(user_messages[0])
            assert_events_equal(events, [
                {'type': 'metadata', 'content': {'thread_id': mock.ANY}},
                *to_message_chunks({'type': 'text', 'content': {'role': 'assistant', 'text': llm_messages[0].content}}),
            ])
            thread_id = events[0]['content']['thread_id']

            events = self.send_message(user_messages[1], thread_id=thread_id)
            assert_events_equal(events, [
                {'type': 'metadata', 'content': {'thread_id': thread_id}},
                *to_message_chunks({'type': 'text', 'content': {'role': 'assistant', 'text': llm_messages[1].content}}),
                {'type': 'tool_call', 'content': copy_keys(llm_messages[1].tool_calls[0], ['id', 'name', 'args']) | {'status': 'pending', 'output': None}},
                {'type': 'tool_call_status', 'content': copy_keys(llm_messages[1].tool_calls[0], ['id', 'name']) | {'status': 'success', 'output': {}}},
                *to_message_chunks({'type': 'text', 'content': {'role': 'assistant', 'text': llm_messages[2].content}}),
            ])

        # Verify chat history
        res = self.client.get(reverse('chatthread-latest', query={'project': self.project.id}))
        assert res.status_code == 200
        assert str(res.data['id']) == thread_id
        assert len(res.data['messages']) == 6
        assert [omit_keys(m, ['id', 'tool_call.timestamp', 'tool_call.content']) for m in res.data['messages']] == [
            {'role': 'user', 'text': user_messages[0]},
            {'role': 'assistant', 'text': llm_messages[0].content},
            {'role': 'user', 'text': user_messages[1]},
            {'role': 'assistant', 'text': llm_messages[1].content},
            {'role': 'tool', 'tool_call': copy_keys(llm_messages[1].tool_calls[0], ['id', 'name', 'args']) | {'status': 'success', 'output': {}}},
            {'role': 'assistant', 'text': llm_messages[2].content},
        ]

        # Verify that the section was updated
        executive_summary.refresh_from_db()
        assert executive_summary.data['executive_summary'] == 'New executive summary'

        # Verify version history
        assert executive_summary.history.count() == 1
        history = executive_summary.history.first()
        assert history.history_type == '~'
        assert history.history_user == self.user
        assert history.custom_fields == executive_summary.custom_fields

    def test_inject_context_middleware(self):
        def assert_injected_message(msg):
            assert msg.type == 'human'
            assert str(self.project.id) in msg.content
            assert 'sections.executive_summary' in msg.content
            assert yaml_indent(self.project.sections.get(section_id='executive_summary').data['executive_summary']) in msg.content

        user_messages = [
            'User message 1',
            'User message 2',
            'User message 3',
        ]
        model = FakeChatModel(messages=iter([
            AIMessage('Response', tool_calls=[ToolCall(id='tool_call_1', name='get_section_data', args={'section_id': 'executive_summary'})]),
            AIMessage('done'),
            AIMessage('Another response'),
            AIMessage('Final response'),
        ]))
        with mock_llm_response(model=model):
            res = self.send_message(user_messages[0], context={'section_id': 'executive_summary'})
            thread_id = res[0]['content']['thread_id']
            self.send_message(user_messages[1], context={'section_id': 'executive_summary'}, thread_id=thread_id)

        # Context messages injected before the last human message
        assert len(model.message_log) == 3

        assert [m.type for m in model.message_log[0]['messages']] == ['system', 'human', 'human', 'human']
        assert 'Project Context' in model.message_log[0]['messages'][1].content
        assert_injected_message(model.message_log[0]['messages'][2])
        assert model.message_log[0]['messages'][3].content == user_messages[0]

        assert [m.type for m in model.message_log[1]['messages']] == ['system', 'human', 'human', 'human', 'ai', 'tool']
        assert_injected_message(model.message_log[1]['messages'][2])
        assert model.message_log[1]['messages'][3].content == user_messages[0]

        assert [m.type for m in model.message_log[2]['messages']] == ['system', 'human', 'human', 'human', 'ai', 'tool', 'ai', 'human']
        assert_injected_message(model.message_log[2]['messages'][2])
        assert model.message_log[2]['messages'][7].content == user_messages[1]

        # Context messages not returned in chat history
        res = self.client.get(reverse('chatthread-detail', kwargs={'pk': thread_id}))
        assert [m['role'] for m in res.data['messages']] == ['user', 'assistant', 'tool', 'assistant', 'user', 'assistant']

    def test_fix_broken_tool_calls_middleware(self):
        with mock_llm_response(messages=[
            AIMessage('call tool', tool_calls=[
                ToolCall(id='tool_call_1', name='get_section_data', args={'section_id': 'executive_summary'}),
            ]),
            AIMessage('done'),
        ]):
            res = self.send_message('Hi')
            thread_id = res[0]['content']['thread_id']

        # Create a broken state
        agent = get_agent('project_agent')
        state = agent.get_state(config={'configurable': {'thread_id': thread_id}})
        state.values['messages'][2].tool_calls[0]['id'] = 'missing_tool_message'
        state.values['messages'][3].tool_call_id = 'missing_tool_call'

        agent.update_state(config=state.config, values={
            'messages': state.values['messages'],
        })

        # Check broken tool calls are fixed
        model = FakeChatModel(messages=iter([AIMessage('final response')]))
        with mock_llm_response(model=model):
            res = self.send_message('Next message', thread_id=thread_id)
            # ToolMessage without ToolCall removed
            assert [m.type for m in model.message_log[0]['messages']] == ['system', 'human', 'human', 'ai', 'ai', 'human']
            # ToolCall without ToolMessage removed
            assert model.message_log[0]['messages'][3].tool_calls == []

        # Fixed in state/history
        state = agent.get_state(config={'configurable': {'thread_id': thread_id}})
        assert [m.type for m in state.values['messages']] == ['human', 'human', 'ai', 'ai', 'human', 'ai']


@pytest.mark.django_db()
class TestProjectAgentTools:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user()
        self.project = create_project(members=[self.user], report_data={
            'field_list': ['first', 'second'],
        })
        self.client = api_client(user=self.user)

        with override_configuration(GUEST_USERS_CAN_EDIT_PROJECTS=False):
            yield

    def run_tool(self, tool, **kwargs):
        runtime = ToolRuntime(
            tool_call_id='tool_call_id_1',
            context=ProjectContext(user_id=str(self.user.id), project_id=str(self.project.id)),
            state=None,
            config={},
            store=None,
            stream_writer=None,
        )
        res = async_to_sync(tool.ainvoke)(
            input=kwargs | {
                'runtime': runtime,
            },
        )
        return res.update['messages'][0].content

    def test_tool_get_section_data(self):
        section = self.project.sections.get(section_id='other')
        contains_infos = [
            f'sections.{section.section_id}',
            section.data['field_string'],
            section.data['field_markdown'],
        ]
        res = self.run_tool(get_section_data, section_id=section.section_id)
        for info in contains_infos:
            assert str(info) in res

    def test_tool_get_finding_data(self):
        finding = self.project.findings.first()
        contains_infos = [
            f'findings.{finding.finding_id}',
            finding.data['field_string'],
            yaml_indent(finding.data['field_markdown']),
        ]
        res = self.run_tool(get_finding_data, finding_id=str(finding.finding_id))
        for info in contains_infos:
            assert str(info) in res

    def test_tool_get_note_data(self):
        note = self.project.notes.first()
        contains_infos = [
            f'notes.{note.note_id}',
            note.title,
            yaml_indent(note.text),
        ]
        res = self.run_tool(get_note_data, note_id=str(note.note_id))
        for info in contains_infos:
            assert str(info) in res

    def test_tool_get_template_data(self):
        template = create_template()
        contains_infos = [
            str(template.id),
            template.main_translation.data['title'],
            yaml_indent(template.main_translation.data['description'], spaces=8),
        ]
        res = self.run_tool(get_template_data, template_id=str(template.id))
        for info in contains_infos:
            assert str(info) in res

    @pytest.mark.parametrize(('search_terms', 'expected_templates'), [
        (None, ['t1', 't2', 't3']),  # List all templates (no search terms)
        ('xss', ['t1']),  # Search by tag
        ('SQL Injection', ['t2']),  # Search by title
        ('web', ['t1', 't3']),  # Search with multiple matches
        ('nonexistent', []),
    ])
    def test_tool_list_templates(self, search_terms, expected_templates):
        templates = {
            't1': create_template(tags=['xss', 'web'], data={'title': 'Cross-Site Scripting'}),
            't2': create_template(tags=['sql', 'database'], data={'title': 'SQL Injection'}),
            't3': create_template(tags=['web', 'csrf'], data={'title': 'CSRF Attack'}),
        }
        res = self.run_tool(list_templates, search_terms=search_terms)

        if expected_templates:
            # Check that expected templates are in results
            for template_name in expected_templates:
                assert str(templates[template_name].id) in res
            # Check that unexpected templates are not in results
            for template_name, template in templates.items():
                if template_name not in expected_templates:
                    assert str(template.id) not in res
        else:
            assert 'No matching templates found' in res

    @pytest.mark.parametrize(('field_path', 'new_value'), [
        # Simple field types
        ('field_string', 'updated string'),
        ('field_markdown', '# Updated markdown'),
        ('field_int', 42),
        ('field_bool', True),
        ('field_enum', 'enum1'),
        ('field_combobox', 'custom value'),
        ('field_date', '2024-12-31'),
        ('field_cvss', 'CVSS:3.1/AV:L/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H'),
        ('field_cwe', 'CWE-79'),
        # Edge cases
        ('field_string', None),
        ('field_string', ''),
        # List field
        ('field_list', ['item1', 'item2', 'item3']),
        # Nested object field
        ('field_object.nested1', 'nested value'),
        ('field_object.field_string', 'nested string'),
        ('field_object.field_int', 999),
        # List of objects - update specific item
        ('field_list.[1]', 'updated'),
    ])
    def test_tool_update_field_value(self, field_path, new_value):
        section = self.project.sections.get(section_id='other')
        section.update_data({
            'field_list': ['first', 'second'],
        })
        section.save()

        res = self.run_tool(update_field_value, path=f'sections.other.data.{field_path}', value=new_value)
        assert res == 'Updated successfully.'

        # Verify the update
        section.refresh_from_db()
        assert get_value_at_path(section.data, tuple(field_path.split('.'))) == new_value

    @pytest.mark.parametrize(('path', 'error_message'), [
        ('sections.data.title', 'Invalid path format'),
        ('sections.executive_summary.title', 'Invalid path format'),
        ('findings.123.title', 'Invalid path format'),
        ('notes.123.data.title', 'Unknown object type'),
        ('findings.nonexistent.data.title', None),
        ('sections.nonexistent.data.title', None),
        ('sections.executive_summary.data.nonexistent_field.nested', None),
    ])
    def test_tool_update_field_value_invalid_paths(self, path, error_message):
        res = self.run_tool(update_field_value, path=path, value='test value')
        assert 'Error:' in res
        if error_message:
            assert error_message in res

    @pytest.mark.parametrize(('initial_value', 'old_text', 'new_text', 'expected_result'), [
        ('# Heading\n\nSome content here.', 'Some content', 'Updated content', '# Heading\n\nUpdated content here.'),
        ('First line\nSecond line', 'First line', 'New first line', 'New first line\nSecond line'),
        ('First line\nSecond line', 'Second line', 'New second line', 'First line\nNew second line'),
        ('Old content', 'Old content', 'Completely new content', 'Completely new content'),
        ('Text to delete\nKeep this', 'Text to delete\n', '', 'Keep this'),
        ('Existing text', 'Existing', 'New existing', 'New existing text'),
        ('test test test', 'test', 'replaced', 'replaced test test'),
        ('```python\nold_code()\n```', 'old_code()', 'new_code()', '```python\nnew_code()\n```'),
        ('Line 1\nLine 2\nLine 3', 'Line 1\nLine 2', 'First\nSecond', 'First\nSecond\nLine 3'),
    ])
    def test_tool_update_markdown_field(self, initial_value, old_text, new_text, expected_result):
        section = self.project.sections.get(section_id='other')
        section.update_data({'field_markdown': initial_value})
        section.save()

        res = self.run_tool(update_markdown_field, path='sections.other.data.field_markdown', old_text=old_text, new_text=new_text)
        assert res == 'Updated successfully'

        section.refresh_from_db()
        assert section.data['field_markdown'] == expected_result

    @pytest.mark.parametrize(('initial_value', 'old_text', 'error_substring'), [
        ('Some content here', 'Non-existent text', 'Could not find'),
        ('Some content', '', 'old_text cannot be empty'),
        ('', 'Some text', 'field is empty'),
        (None, 'Some text', 'field is empty'),
        ('Hello World', 'hello', 'Could not find'),
    ])
    def test_tool_update_markdown_field_errors(self, initial_value, old_text, error_substring):
        section = self.project.sections.get(section_id='other')
        section.update_data({'field_markdown': initial_value})
        section.save()

        res = self.run_tool(update_markdown_field, path='sections.other.data.field_markdown', old_text=old_text, new_text='new text')
        assert 'Error:' in res
        assert error_substring in res

    def test_tool_update_markdown_field_non_markdown_field(self):
        res = self.run_tool(update_markdown_field, path='sections.other.data.field_string', old_text='old', new_text='new')
        assert 'Error:' in res
        assert 'not of type markdown' in res

    def test_tool_create_finding_empty(self):
        initial_count = self.project.findings.count()
        res = self.run_tool(create_finding, data=None, template_id=None, template_language=None)

        assert 'Successfully created finding' in res
        assert self.project.findings.count() == initial_count + 1

        finding = self.project.findings.order_by('-created').first()
        assert finding is not None
        # Verify finding data is in response
        assert str(finding.finding_id) in res

    def test_tool_create_finding_with_data(self):
        initial_count = self.project.findings.count()
        finding_data = {
            'title': 'Custom Finding Title',
            'cvss': 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H',
            'description': 'Custom description',
        }
        res = self.run_tool(create_finding, data=finding_data, template_id=None, template_language=None)

        assert 'Successfully created finding' in res
        assert self.project.findings.count() == initial_count + 1

        finding = self.project.findings.order_by('-created').first()
        assert finding.data['title'] == 'Custom Finding Title'
        assert finding.data['cvss'] == 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H'
        assert finding.data['description'] == 'Custom description'

    def test_tool_create_finding_from_template(self):
        template = create_template(data={
            'title': 'Template Title',
            'description': 'Template Description',
            'recommendation': 'Template Recommendation',
        })
        initial_count = self.project.findings.count()

        res = self.run_tool(create_finding, data=None, template_id=str(template.id), template_language=None)

        assert 'Successfully created finding' in res
        assert self.project.findings.count() == initial_count + 1

        finding = self.project.findings.order_by('-created').first()
        assert finding.data['title'] == 'Template Title'
        assert finding.data['description'] == 'Template Description'
        assert finding.data['recommendation'] == 'Template Recommendation'
        assert finding.template_id == template.id

    def test_tool_create_finding_from_template_with_override(self):
        template = create_template(data={
            'title': 'Template Title',
            'description': 'Template Description',
            'recommendation': 'Template Recommendation',
        })
        initial_count = self.project.findings.count()
        override_data = {
            'title': 'Overridden Title',
            'description': 'Overridden Description',
        }

        res = self.run_tool(create_finding, data=override_data, template_id=str(template.id), template_language=None)

        assert 'Successfully created finding' in res
        assert self.project.findings.count() == initial_count + 1

        finding = self.project.findings.order_by('-created').first()
        assert finding.data['title'] == 'Overridden Title'
        assert finding.data['description'] == 'Overridden Description'
        # Non-overridden field should come from template
        assert finding.data['recommendation'] == 'Template Recommendation'
        assert finding.template_id == template.id


@pytest.mark.django_db()
class TestAgentPermissions:
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
    @override_configuration(GUEST_USERS_CAN_EDIT_PROJECTS=False)
    def test_api_permissions(self, user_name, project_name, expected_read, expected_write):
        users = {
            'member': create_user(),
            'guest': create_user(is_guest=True),
            'admin': create_user(is_superuser=True, admin_permissions_enabled=True),
            'unauthorized': create_user(),
            'anonymous': AnonymousUser(),
        }
        user = users[user_name]
        client = api_client(user)
        project = {
            'project': create_project(members=[users['member'], users['guest']]),
            'readonly': create_project(members=[users['member'], users['guest']], readonly=True),
        }[project_name]

        thread = ChatThread.objects.create(
            user=user if user.is_authenticated else users['member'],
            project=project,
        )
        agent = get_agent('project_ask')
        agent.update_state(config={'configurable': {'thread_id': str(thread.id)}}, values={
            'messages': [
                HumanMessage(content='request'),
                AIMessage(content='response'),
            ],
        })

        # Agent permissions
        for thread_id in [None, thread.id]:
            with mock_llm_response(messages=[
                AIMessage(content='dummy', tool_calls=[
                    ToolCall(id='tool_call_1', name='update_field_value', args={'path': 'sections.executive_summary.data.executive_summary', 'value': 'updated'}),
                ]),
                AIMessage(content='done'),
            ]):
                res = client.post(reverse('chatthread-list'), data={
                    'id': thread_id,
                    'agent': 'project_agent',
                    'project': project.id,
                    'messages': ['dummy'],
                    'context': {},
                })
                if expected_read:
                    assert res.status_code == 200
                    events = parse_sse_events(res)
                    tool_status = next(e for e in events if e['type'] == 'tool_call_status')['content']['status']
                    assert tool_status == ('success' if expected_write else 'error')
                else:
                    assert res.status_code in [400, 403]

        # ChatThread history permissions
        res_thread = client.get(reverse('chatthread-detail', kwargs={'pk': thread.id}))
        assert res_thread.status_code in ([200] if expected_read else [403, 404])

        res_latest = client.get(reverse('chatthread-latest', query={'project': project.id}))
        assert res_latest.status_code in ([200] if expected_read else [403, 404])


@pytest.mark.django_db()
class TestAiCleanupTask:
    def checkpoint_exists(self, checkpoint):
        return LangchainCheckpoint.objects.filter(id=checkpoint.id).exists()

    def test_cleanup_old_langchain_checkpoints(self):
        with mock_time(before=timedelta(days=2)):
            thread = ChatThread.objects.create(
                user=create_user(),
                project=create_project(),
            )
            old_checkpoint = LangchainCheckpoint.objects.create(thread=thread)
            current_checkpoint = LangchainCheckpoint.objects.create(thread=thread)

        async_to_sync(cleanup_old_langchain_checkpoints)(task_info=PeriodicTaskInfo(
            spec=next(filter(lambda t: t.id == 'cleanup_old_langchain_checkpoints', periodic_task_registry.tasks)),
            model=PeriodicTask(last_success=None),
        ))
        assert not self.checkpoint_exists(old_checkpoint)
        assert self.checkpoint_exists(current_checkpoint)

