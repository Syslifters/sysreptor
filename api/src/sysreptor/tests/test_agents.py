import contextlib
import json
import re
import textwrap
from datetime import timedelta
from unittest import mock
from uuid import uuid4

import pytest
from asgiref.sync import async_to_sync
from deepagents.backends import CompositeBackend, StateBackend
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from langchain.messages import AIMessage, AIMessageChunk, HumanMessage, ToolCall
from langchain.tools import ToolRuntime
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.outputs.chat_generation import ChatGenerationChunk
from langgraph.checkpoint.base import WRITES_IDX_MAP

from sysreptor.ai.agents import get_agent
from sysreptor.ai.agents.base import (
    get_default_model_id,
    get_model_configs,
    init_chat_model,
)
from sysreptor.ai.agents.checkpointer import DjangoModelCheckpointer
from sysreptor.ai.agents.filesystem import (
    NotesAgentsDirBackend,
    ProjectFilesystemBackend,
)
from sysreptor.ai.agents.middleware import SelectConfiguredModelMiddleware
from sysreptor.ai.agents.project import ProjectContext
from sysreptor.ai.agents.tools import analyze_image
from sysreptor.ai.agents.tools_project import (
    create_finding,
    create_note,
    list_notes,
    list_templates,
    read_template,
    update_field_value,
    update_markdown_field,
)
from sysreptor.ai.models import ChatThread, LangchainCheckpoint, LangchainCheckpointBlob, LangchainCheckpointWrite
from sysreptor.ai.tasks import cleanup_old_langchain_checkpoints
from sysreptor.conf.settings import validate_ai_agent_models
from sysreptor.pentests.models import NoteType
from sysreptor.tasks.models import PeriodicTask, PeriodicTaskInfo, periodic_task_registry
from sysreptor.tests.mock import (
    api_client,
    create_project,
    create_projectnotebookpage,
    create_template,
    create_user,
    mock_time,
    override_configuration,
)
from sysreptor.utils.fielddefinition.utils import get_value_at_path
from sysreptor.utils.utils import copy_keys, merge, omit_keys


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
    SelectConfiguredModelMiddleware._model_cache.clear()
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
    out.append(event | {'content': omit_keys(event['content'], ['text', 'reasoning']) | {'id': mock.ANY, 'timestamp': mock.ANY}})
    return out


def assert_events_equal(actual, expected):
    assert len(actual) == len(expected)
    ignore_keys = ['content.id', 'content.timestamp', 'content.content']
    default_values = {'subagent': None}
    for a, e in zip(actual, expected, strict=True):
        assert merge(default_values, omit_keys(a, ignore_keys)) == merge(default_values, omit_keys(e, ignore_keys))


def yaml_indent(text: str, spaces: int = 4) -> str:
    return '\n'.join((' ' * spaces) + line if (line and idx > 0) else '' for idx, line in enumerate(text.splitlines()))


def finding_path(finding_id) -> str:
    return f'/project/reporting/findings/{finding_id}.yaml'


def section_path(section_id) -> str:
    return f'/project/reporting/sections/{section_id}.yaml'


def note_path(note_id) -> str:
    return f'/project/notes/{note_id}.yaml'


@contextlib.contextmanager
def project_filesystem_runtime(project, user):
    with mock.patch('sysreptor.ai.agents.filesystem.get_runtime') as m:
        m.return_value = mock.Mock(context=ProjectContext(
            project_id=str(project.id),
            user_id=str(user.id),
        ))
        yield


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
                ToolCall(id='tool_call_1', name='update_field_value', args={
                    'file_path': '/project/reporting/sections/executive_summary.yaml',
                    'field': 'data.executive_summary',
                    'value': 'New executive summary',
                }),
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
        assert [omit_keys(m, ['id', 'timestamp', 'tool_call.timestamp', 'tool_call.content']) for m in res.data['messages']] == [
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

        tool_msg = next(m for m in res.data['messages'] if m['role'] == 'tool')
        from django.utils.dateparse import parse_datetime
        tool_ts = parse_datetime(tool_msg['tool_call']['timestamp'])
        assert tool_ts < history.history_date

    def test_inject_context_middleware(self):
        finding = self.project.findings.first()

        def assert_injected_message(msg):
            assert msg.type == 'human'
            assert str(self.project.id) in msg.content
            assert '/project/reporting/sections/executive_summary.yaml' in msg.content
            assert yaml_indent(self.project.sections.get(section_id='executive_summary').data['executive_summary']) in msg.content

        user_messages = [
            'User message 1',
            'User message 2',
            'User message 3',
        ]
        model = FakeChatModel(messages=iter([
            AIMessage('Response', tool_calls=[ToolCall(id='tool_call_1', name='read_file', args={'file_path': '/project/reporting/sections/executive_summary.yaml'})]),
            AIMessage('done'),
            AIMessage('Another response'),
            AIMessage('Final response'),
        ]))
        with mock_llm_response(model=model):
            res = self.send_message(user_messages[0], context={'section_id': 'executive_summary'})
            thread_id = res[0]['content']['thread_id']
            self.send_message(user_messages[1], context={'section_id': 'executive_summary'}, thread_id=thread_id)
            self.send_message(user_messages[2], context={'finding_id': finding.finding_id}, thread_id=thread_id)

        # Injected context is merged with user messages before the LLM call
        assert len(model.message_log) == 4

        assert [m.type for m in model.message_log[0]['messages']] == ['system', 'human']
        assert '<navigation file="/project/reporting/sections/executive_summary.yaml">' in model.message_log[0]['messages'][1].content
        assert_injected_message(model.message_log[0]['messages'][1])
        assert user_messages[0] in model.message_log[0]['messages'][1].content

        assert [m.type for m in model.message_log[1]['messages']] == ['system', 'human', 'ai', 'tool']
        assert_injected_message(model.message_log[1]['messages'][1])
        assert user_messages[0] in model.message_log[1]['messages'][1].content

        assert [m.type for m in model.message_log[2]['messages']] == ['system', 'human', 'ai', 'tool', 'ai', 'human']
        assert_injected_message(model.message_log[2]['messages'][1])
        assert user_messages[1] in model.message_log[2]['messages'][5].content

        # Page switched to finding
        assert [m.type for m in model.message_log[3]['messages']] == ['system', 'human', 'ai', 'tool', 'ai', 'human', 'ai', 'human']
        finding_message = model.message_log[3]['messages'][7]
        assert f'<navigation file="/project/reporting/findings/{finding.finding_id}.yaml">' in finding_message.content
        assert finding.title in finding_message.content
        assert yaml_indent(finding.data['description']) in finding_message.content
        assert user_messages[2] in finding_message.content

        # Context messages not returned in chat history
        res = self.client.get(reverse('chatthread-detail', kwargs={'pk': thread_id}))
        assert [m['role'] for m in res.data['messages']] == ['user', 'assistant', 'tool', 'assistant', 'user', 'assistant', 'user', 'assistant']

    def test_subagents(self):
        subagent_tool_call_id = 'subagent_tool_call_1'
        subagent_inner_tool_call_id = 'subagent_inner_tool_1'
        task_call = ToolCall(id=subagent_tool_call_id, name='task', args={'subagent_type': 'general-purpose', 'description': 'Test subagent'})
        read_section_call = ToolCall(id=subagent_inner_tool_call_id, name='read_file', args={'file_path': '/project/reporting/sections/executive_summary.yaml'})
        llm_messages = [
            AIMessage(content='', tool_calls=[task_call]),
            AIMessage(content='Subagent started', tool_calls=[read_section_call]),
            AIMessage(content='Subagent done'),
            AIMessage(content='Done.'),
        ]
        with mock_llm_response(messages=llm_messages):
            events = self.send_message('Use a subagent')

        assert_events_equal(events, [
            {'type': 'metadata', 'content': {'thread_id': mock.ANY}},
            {'type': 'tool_call', 'content': copy_keys(task_call, ['id', 'name', 'args']) | {'status': 'pending', 'output': None}},
            *to_message_chunks({'type': 'text', 'content': {'role': 'assistant', 'text': llm_messages[1].content}, 'subagent': subagent_tool_call_id}),
            {'type': 'tool_call', 'content': copy_keys(read_section_call, ['id', 'name', 'args']) | {'status': 'pending', 'output': None}, 'subagent': subagent_tool_call_id},
            {'type': 'tool_call_status', 'content': copy_keys(read_section_call, ['id', 'name']) | {'status': 'success'}, 'subagent': subagent_tool_call_id},
            *to_message_chunks({'type': 'text', 'content': {'role': 'assistant', 'text': llm_messages[2].content}, 'subagent': subagent_tool_call_id}),
            {'type': 'tool_call_status', 'content': copy_keys(task_call, ['id', 'name']) | {'status': 'success'}},
            *to_message_chunks({'type': 'text', 'content': {'role': 'assistant', 'text': llm_messages[3].content}}),
        ])

    def test_subagent_error_does_not_abort_main_agent(self):
        subagent_tool_call_id = 'subagent_tool_call_fail'
        task_call = ToolCall(
            id=subagent_tool_call_id,
            name='task',
            args={'subagent_type': 'general-purpose', 'description': 'Failing subagent'},
        )

        class FailThenContinueMessages:
            """Main task call, then ModelRetryMiddleware attempts raise, then main continues."""

            def __init__(self):
                self._items = iter([
                    AIMessage(content='', tool_calls=[task_call]),
                    'fail',
                    'fail',
                    'fail',
                    AIMessage(content='Continued after subagent error.'),
                ])

            def __iter__(self):
                return self

            def __next__(self):
                item = next(self._items)
                if item == 'fail':
                    raise RuntimeError('Simulated subagent LLM failure')
                return item

        with (
            mock.patch('langchain.agents.middleware.model_retry.calculate_delay', return_value=0),
            mock_llm_response(messages=FailThenContinueMessages()),
        ):
            events = self.send_message('Use a failing subagent')

        assert not any(e['type'] == 'error' for e in events)
        task_status = next(
            e for e in events
            if e['type'] == 'tool_call_status' and e['content'].get('id') == subagent_tool_call_id
        )
        assert task_status['content']['status'] == 'error'
        assert task_status['content']['content'] == 'Error: Internal server error'
        assert_events_equal(events, [
            {'type': 'metadata', 'content': {'thread_id': mock.ANY}},
            {'type': 'tool_call', 'content': copy_keys(task_call, ['id', 'name', 'args']) | {'status': 'pending', 'output': None}},
            {'type': 'tool_call_status', 'content': copy_keys(task_call, ['id', 'name']) | {'status': 'error'}},
            *to_message_chunks({'type': 'text', 'content': {'role': 'assistant', 'text': 'Continued after subagent error.'}}),
        ])


@pytest.mark.django_db()
class TestAskUserInterrupts:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user()
        self.project = create_project(members=[self.user])
        self.client = api_client(user=self.user)

    def send_message(self, message: str, thread_id: str = None):
        res = self.client.post(reverse('chatthread-list'), data={
            'id': thread_id,
            'agent': 'project_ask',
            'project': self.project.id,
            'messages': [message],
            'context': {},
        })
        assert res.status_code == 200
        return parse_sse_events(res)

    def send_resume(self, resume, thread_id: str):
        res = self.client.post(reverse('chatthread-list'), data={
            'id': thread_id,
            'agent': 'project_ask',
            'project': self.project.id,
            'resume': resume,
            'context': {},
        })
        assert res.status_code == 200
        return parse_sse_events(res)

    def test_ask_user_interrupt_flow(self):
        options = [
            'Executive summary only',
            'Full technical report',
        ]
        ask_user_call = ToolCall(
            id='tool_call_ask_user',
            name='ask_user',
            args={
                'question': 'Which report style?',
                'options': options,
            },
        )
        llm_messages = [
            AIMessage(content='I need clarification.', tool_calls=[ask_user_call]),
            AIMessage(content='Using executive summary only.'),
            AIMessage(content='Let me ask again.', tool_calls=[ask_user_call]),
            AIMessage(content='Okay, continuing without the style.'),
        ]

        with mock_llm_response(messages=llm_messages):
            events = self.send_message('Write the report')
            thread_id = events[0]['content']['thread_id']
            interrupt_event = next(e for e in events if e['type'] == 'interrupt')
            interrupt_id = interrupt_event['content'][0]['id']
            assert interrupt_event['content'][0]['value'] == {
                'interrupt_type': 'ask_user',
                'question': 'Which report style?',
                'options': options,
            }

            res = self.client.get(reverse('chatthread-detail', kwargs={'pk': thread_id}))
            assert res.status_code == 200
            assert res.data['interrupts'] == interrupt_event['content']

            events = self.send_resume({
                interrupt_id: 'Executive summary only',
            }, thread_id=thread_id)
            assert not any(e['type'] == 'interrupt' for e in events)
            tool_status = next(e for e in events if e['type'] == 'tool_call_status')
            assert tool_status['content']['name'] == 'ask_user'
            assert tool_status['content']['status'] == 'success'
            content = tool_status['content']['content']
            assert content == 'User answered: Executive summary only'
            assert tool_status['content']['output'] == {
                'answer': 'Executive summary only',
            }

            res = self.client.get(reverse('chatthread-detail', kwargs={'pk': thread_id}))
            assert res.status_code == 200
            assert res.data['interrupts'] == []
            tool_msg = next(
                m for m in res.data['messages']
                if m.get('role') == 'tool' and m.get('tool_call', {}).get('name') == 'ask_user'
            )
            assert tool_msg['tool_call']['status'] == 'success'
            assert tool_msg['tool_call']['content'] == content

            events = self.send_message('Ask again', thread_id=thread_id)
            assert any(e['type'] == 'interrupt' for e in events)

            events = self.send_message('Never mind', thread_id=thread_id)
            assert not any(e['type'] == 'interrupt' for e in events)
            assert any(e['type'] == 'text' for e in events)

            res = self.client.get(reverse('chatthread-detail', kwargs={'pk': thread_id}))
            assert res.status_code == 200
            assert res.data['interrupts'] == []


@pytest.mark.django_db()
class TestProjectAgentTools:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user()
        self.project = create_project(
            members=[self.user],
            images_kwargs=[{'name': 'image.png'}],
            report_data={
                'field_list': ['first', 'second'],
            })
        self.client = api_client(user=self.user)

        with override_configuration(GUEST_USERS_CAN_EDIT_PROJECTS=False):
            yield

    def run_tool(self, tool, model=None, **kwargs):
        return self.run_tool_message(tool, model=model, **kwargs).content

    def run_tool_message(self, tool, model=None, **kwargs):
        runtime = ToolRuntime(
            tool_call_id='tool_call_id_1',
            context=ProjectContext(
                user_id=str(self.user.id),
                project_id=str(self.project.id),
                model=model,
            ),
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
        return res.update['messages'][0]

    def test_tool_list_notes(self):
        contains_infos = [
            *[n.title for n in self.project.notes.all()],
            *[n.note_id for n in self.project.notes.all()],
        ]
        res = self.run_tool(list_notes)
        for info in contains_infos:
            assert str(info) in res

    def test_tool_read_template(self):
        template = create_template()
        contains_infos = [
            str(template.id),
            template.main_translation.data['title'],
            yaml_indent(template.main_translation.data['description'], spaces=8),
        ]
        res = self.run_tool(read_template, template_id=str(template.id))
        for info in contains_infos:
            assert str(info) in res

    @pytest.mark.parametrize(('search_terms', 'expected_templates'), [
        ('', ['t1', 't2', 't3']),  # List all templates (no search terms)
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
        ('field_json', '{"key": "value"}'),
        # Edge cases
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

        res = self.run_tool(
            update_field_value,
            file_path='/project/reporting/sections/other.yaml',
            field=f'data.{field_path}',
            value=new_value,
        )
        assert res == 'Updated successfully.'

        # Verify the update
        section.refresh_from_db()
        assert get_value_at_path(section.data, tuple(field_path.split('.'))) == new_value

    @pytest.mark.parametrize(('file_path', 'field', 'error_message'), [
        ('/project/unknown/x.yaml', 'data.title', 'File not found'),
        ('/project/reporting/sections/executive_summary.yaml', 'title', 'Currently only "data" field updates are supported'),
        ('/project/reporting/sections/nonexistent.yaml', 'data.title', None),
        ('/project/reporting/findings/nonexistent.yaml', 'data.title', None),
        ('/project/reporting/sections/executive_summary.yaml', 'data.nonexistent_field.nested', None),
        ('/project/notes/nonexistent.yaml', 'title', None),
    ])
    def test_tool_update_field_value_invalid_paths(self, file_path, field, error_message):
        res = self.run_tool(update_field_value, file_path=file_path, field=field, value='test value')
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

        res = self.run_tool(
            update_markdown_field,
            file_path='/project/reporting/sections/other.yaml',
            field='data.field_markdown',
            old_text=old_text,
            new_text=new_text,
        )
        assert res == 'Updated successfully'

        section.refresh_from_db()
        assert section.data['field_markdown'] == expected_result

    @pytest.mark.parametrize(('field', 'new_value'), [
        ('title', 'Updated note title'),
        ('text', 'Updated note text'),
    ])
    def test_tool_update_field_value_note(self, field, new_value):
        note = create_projectnotebookpage(
            project=self.project,
            title='Original title',
            text='Original note text',
            checked=False,
            icon_emoji=None,
        )

        res = self.run_tool(
            update_field_value,
            file_path=note_path(note.note_id),
            field=field,
            value=new_value,
        )
        assert res == 'Updated successfully.'

        note.refresh_from_db()
        assert getattr(note, field) == new_value

    @pytest.mark.parametrize(('initial_value', 'old_text', 'new_text', 'expected_result'), [
        ('# Note\n\nSome content here.', 'Some content', 'Updated content', '# Note\n\nUpdated content here.'),
        ('First paragraph\n\nSecond paragraph', 'First paragraph', 'New first paragraph', 'New first paragraph\n\nSecond paragraph'),
    ])
    def test_tool_update_markdown_field_note(self, initial_value, old_text, new_text, expected_result):
        note = create_projectnotebookpage(project=self.project, text=initial_value)

        res = self.run_tool(
            update_markdown_field,
            file_path=note_path(note.note_id),
            field='text',
            old_text=old_text,
            new_text=new_text,
        )
        assert res == 'Updated successfully'

        note.refresh_from_db()
        assert note.text == expected_result

    def test_tool_update_note_text_excalidraw_denied(self):
        note = create_projectnotebookpage(
            project=self.project,
            type=NoteType.EXCALIDRAW,
            excalidraw_data={'elements': [{'id': 'e1'}]},
        )
        res = self.run_tool(
            update_field_value,
            file_path=note_path(note.note_id),
            field='text',
            value='attempted write',
        )
        assert 'Error:' in res
        assert 'excalidraw' in res.lower()

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

        res = self.run_tool(
            update_markdown_field,
            file_path='/project/reporting/sections/other.yaml',
            field='data.field_markdown',
            old_text=old_text,
            new_text='new text',
        )
        assert 'Error:' in res
        assert error_substring in res

    def test_tool_update_markdown_field_non_markdown_field(self):
        res = self.run_tool(
            update_markdown_field,
            file_path='/project/reporting/sections/other.yaml',
            field='data.field_string',
            old_text='old',
            new_text='new',
        )
        assert 'Error:' in res
        assert 'not of type markdown' in res

    def test_tool_create_finding_empty(self):
        initial_count = self.project.findings.count()
        res = self.run_tool(create_finding)

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
        res = self.run_tool(create_finding, data=finding_data)

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

        res = self.run_tool(create_finding, data={}, template_id=str(template.id))

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

        res = self.run_tool(create_finding, data=override_data, template_id=str(template.id))

        assert 'Successfully created finding' in res
        assert self.project.findings.count() == initial_count + 1

        finding = self.project.findings.order_by('-created').first()
        assert finding.data['title'] == 'Overridden Title'
        assert finding.data['description'] == 'Overridden Description'
        # Non-overridden field should come from template
        assert finding.data['recommendation'] == 'Template Recommendation'
        assert finding.template_id == template.id

    def test_tool_create_note(self):
        initial_count = self.project.notes.count()
        res = self.run_tool(create_note, data={'title': 'Agent Note', 'text': 'Note content from agent'})

        assert 'Successfully created note' in res
        assert self.project.notes.count() == initial_count + 1

        note = self.project.notes.order_by('-created').first()
        assert note.title == 'Agent Note'
        assert note.text == 'Note content from agent'
        assert note.parent is None
        assert str(note.note_id) in res

    def test_tool_create_note_with_parent_and_order(self):
        parent = create_projectnotebookpage(project=self.project, title='Parent note', order=1)
        sibling = create_projectnotebookpage(project=self.project, parent=parent, title='Sibling', order=1, text='sibling')

        res = self.run_tool(
            create_note,
            data={'title': 'Child note', 'text': 'Nested content'},
            parent=str(parent.note_id),
            order=1,
        )

        assert 'Successfully created note' in res
        note = self.project.notes.order_by('-created').first()
        assert note.title == 'Child note'
        assert note.text == 'Nested content'
        assert note.parent_id == parent.id
        assert note.order == 1

        sibling.refresh_from_db()
        assert sibling.order == 2

    @pytest.mark.parametrize(('image_ref', 'expected'), [
        ('image.png', True),
        ('/images/name/image.png', True),
        ('![shot](/images/name/image.png)', True),
        ('![shot](/images/name/image.png){width="auto"}', True),
        ('missing.png', False),
        ('/images/name/missing.png', False),
    ])
    def test_tool_analyze_image_success(self, image_ref, expected):
        fake_agent = mock.Mock()
        fake_agent.ainvoke = mock.AsyncMock(return_value={
            'messages': [AIMessage(content='Screenshot shows SQL error on login form')],
        })
        with mock.patch('sysreptor.ai.agents.tools.create_agent', return_value=fake_agent):
            msg = self.run_tool_message(analyze_image, image=image_ref, prompt='What error is shown?')

        if expected:
            assert msg.status == 'success'
            assert msg.content == 'Screenshot shows SQL error on login form'
            assert msg.additional_kwargs['output'] == {
                'image': 'image.png',
                'model': 'test:fake-model',
            }
        else:
            assert msg.status == 'error'


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
                    ToolCall(id='tool_call_1', name='update_field_value', args={
                        'file_path': '/project/reporting/sections/executive_summary.yaml',
                        'field': 'data.executive_summary',
                        'value': 'updated',
                    }),
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
    def test_cleanup_old_langchain_checkpoints(self):
        with mock_time(before=timedelta(days=2)):
            thread = ChatThread.objects.create(user=create_user(), project=create_project())
            old = LangchainCheckpoint.objects.create(
                thread=thread,
                checkpoint={'id': str(uuid4()), 'channel_versions': {'messages': '1'}, 'channel_values': {}},
            )
            old_write = LangchainCheckpointWrite.objects.create(
                thread=thread, checkpoint_ns='', checkpoint_id=old.checkpoint_id,
                task_id='t1', idx=0, channel='messages', type='json', blob=b'"old"',
            )
            unreferenced_blob = LangchainCheckpointBlob.objects.create(
                thread=thread, checkpoint_ns='',
                channel='messages', version='1', type='json', blob=b'"v1"',
            )

            current = LangchainCheckpoint.objects.create(
                thread=thread,
                checkpoint={'id': str(uuid4()), 'channel_versions': {'messages': '2'}, 'channel_values': {}},
            )
            current_write = LangchainCheckpointWrite.objects.create(
                thread=thread, checkpoint_ns='', checkpoint_id=current.checkpoint_id,
                task_id='t2', idx=0, channel='messages', type='json', blob=b'"cur"',
            )
            referenced_blob = LangchainCheckpointBlob.objects.create(
                thread=thread, checkpoint_ns='',
                channel='messages', version='2', type='json', blob=b'"v2"',
            )

        cleanup_old_langchain_checkpoints(task_info=PeriodicTaskInfo(
            spec=next(filter(lambda t: t.id == 'cleanup_old_langchain_checkpoints', periodic_task_registry.tasks)),
            model=PeriodicTask(last_success=None),
        ))

        assert not LangchainCheckpoint.objects.filter(pk=old.pk).exists()
        assert not LangchainCheckpointWrite.objects.filter(pk=old_write.pk).exists()
        assert not LangchainCheckpointBlob.objects.filter(pk=unreferenced_blob.pk).exists()

        assert LangchainCheckpoint.objects.filter(pk=current.pk).exists()
        assert LangchainCheckpointWrite.objects.filter(pk=current_write.pk).exists()
        assert LangchainCheckpointBlob.objects.filter(pk=referenced_blob.pk).exists()


@pytest.mark.django_db()
class TestLLMConfig:
    @override_configuration(AI_AGENT_MODELS=[])
    @mock.patch.dict('os.environ', {'AI_AGENT_MODEL': ''})
    def test_no_models_configured(self):
        assert get_model_configs() == []
        with pytest.raises(ValueError, match='No LLM model configured'):
            get_default_model_id()
        with pytest.raises(ValueError, match='Unknown model: test:fake-model'):
            init_chat_model('test:fake-model')

    @override_configuration(AI_AGENT_MODELS=[])
    @mock.patch.dict('os.environ', {'AI_AGENT_MODEL': 'deepseek:gpt-oss-120b', 'DEEPSEEK_API_KEY': 'dummy-key', 'DEEPSEEK_API_BASE': 'https://llm.example.com/'})
    def test_env_fallback(self):
        models = get_model_configs()
        assert models == [{
            'id': 'gpt-oss-120b',
            'model': 'gpt-oss-120b',
            'provider': 'deepseek',
            'api_key': 'dummy-key',
            'base_url': 'https://llm.example.com/',
        }]
        assert get_default_model_id() == 'gpt-oss-120b'

    @override_configuration(AI_AGENT_MODELS=[
        json.dumps({
            'id': 'model-a',
            'label': 'Model A',
            'provider': 'deepseek',
            'model': 'gpt-oss-120b',
            'api_key': 'dummy-key',
            'base_url': 'https://llm.example.com/',
            'temperature': 0.5,
        }),
        json.dumps({
            'id': 'model-b',
            'provider': 'anthropic',
            'model': 'claude-opus-4-8',
            'api_key': 'dummy-key',
        }),
    ])
    def test_db_models(self):
        models = get_model_configs()
        assert len(models) == 2
        assert get_default_model_id() == 'model-a'
        assert api_client(create_user()).get(reverse('publicutils-settings')).data['ai_agent_models'] == [
            {'id': 'model-a', 'label': 'Model A'},
            {'id': 'model-b', 'label': 'model-b'},
        ]

    @pytest.mark.parametrize(('vision_model', 'expected'), [
        (True, 'main-model'),
        ('vision-model', 'vision-model'),
        (False, False),
        (None, False),
        ('missing-vision', False),
    ])
    def test_vision_model_config(self, vision_model, expected):
        models = [
            {'id': 'main-model', 'provider': 'test', 'model': 'main-model', 'api_key': 'k', 'vision_model': vision_model},
            {'id': 'vision-model', 'provider': 'test', 'model': 'vision-model', 'api_key': 'k', 'hidden': True},
        ]
        assert validate_ai_agent_models([json.dumps(m) for m in models]) is (
            not isinstance(vision_model, str) or vision_model in {m['id'] for m in models}
        )

        user = create_user()
        project = create_project(members=[user])
        fake_agent = mock.Mock(ainvoke=mock.AsyncMock(return_value={'messages': [AIMessage(content='ok')]}))
        with (
            mock.patch('sysreptor.ai.agents.tools.get_model_configs', return_value=models),
            mock.patch('sysreptor.ai.agents.tools.init_chat_model', return_value=mock.Mock()) as init_mock,
            mock.patch('sysreptor.ai.agents.tools.create_agent', return_value=fake_agent),
        ):
            msg = async_to_sync(analyze_image.ainvoke)({
                'image': 'file0.png',
                'runtime': ToolRuntime(
                    tool_call_id='t1',
                    context=ProjectContext(user_id=str(user.id), project_id=str(project.id), model='main-model'),
                    state=None, config={}, store=None, stream_writer=None,
                ),
            }).update['messages'][0]

        if expected:
            assert msg.status == 'success'
            assert init_mock.call_args.args == (expected,)
            assert msg.additional_kwargs['output']['model'] == expected
        else:
            assert msg.status == 'error'

    @override_configuration(AI_AGENT_MODELS=[
        json.dumps({
            'id': 'vision-only',
            'provider': 'test',
            'model': 'vision-only',
            'api_key': 'k',
            'hidden': True,
        }),
        json.dumps({
            'id': 'main-model',
            'label': 'Main Model',
            'provider': 'test',
            'model': 'main-model',
            'api_key': 'k',
            'vision_model': 'vision-only',
        }),
    ])
    def test_hidden_models(self):
        assert len(get_model_configs()) == 2
        assert len(get_model_configs(include_hidden=False)) == 1
        assert get_default_model_id() == 'main-model'
        assert api_client(create_user()).get(reverse('publicutils-settings')).data['ai_agent_models'] == [
            {'id': 'main-model', 'label': 'Main Model'},
        ]


@pytest.mark.django_db()
class TestLLMModelSelection:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user()
        self.project = create_project(members=[self.user])
        self.client = api_client(user=self.user)

    def send_message(self, message: str, model: str = None, thread_id: str = None):
        data = {
            'agent': 'project_ask',
            'project': self.project.id,
            'messages': [message],
            'context': {},
        }
        if model is not None:
            data['model'] = model
        if thread_id is not None:
            data['id'] = thread_id
        return self.client.post(reverse('chatthread-list'), data=data)

    @pytest.mark.parametrize(('model', 'expected'), [
        ('model-a', True),
        (None, True), # Use default model
        ('unknown', False),
        ('hidden-model', False),
    ])
    @override_configuration(AI_AGENT_MODELS=[
        json.dumps({'id': 'model-a', 'provider': 'test', 'model': 'model-a', 'api_key': 'fake-key'}),
        json.dumps({'id': 'model-b', 'provider': 'test', 'model': 'model-b', 'api_key': 'fake-key'}),
        json.dumps({'id': 'hidden-model', 'provider': 'test', 'model': 'hidden-model', 'api_key': 'fake-key', 'hidden': True}),
    ])
    def test_model_selection(self, model, expected):
        with mock_llm_response(messages=[AIMessage(content='Hello')]):
            res = self.send_message('Hi', model=model)
            if expected:
                assert res.status_code == 200
                events = parse_sse_events(res)
                assert events[0]['content']['thread_id']
            else:
                assert res.status_code == 400

    @override_configuration(AI_AGENT_MODELS=[
        json.dumps({'id': 'model-a', 'provider': 'test', 'model': 'model-a', 'api_key': 'fake-key'}),
        json.dumps({'id': 'model-b', 'provider': 'test', 'model': 'model-a', 'api_key': 'fake-key'}),
    ])
    def test_switch_model_on_existing_thread(self):
        with mock_llm_response(messages=[AIMessage(content='Hello')]):
            res = self.send_message('Hi', model='model-a')
            assert res.status_code == 200
            thread_id = parse_sse_events(res)[0]['content']['thread_id']

        with mock_llm_response(messages=[AIMessage(content='Hello again')]):
            res = self.send_message('Follow up', model='model-b', thread_id=thread_id)
            assert res.status_code == 200


@pytest.mark.django_db()
class TestProjectFilesystemBackend:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user()
        self.project = create_project(members=[self.user])
        self.backend = CompositeBackend(
            default=StateBackend(),
            routes={ProjectFilesystemBackend.PROJECT_ROOT: ProjectFilesystemBackend()},
        )
        with project_filesystem_runtime(self.project, self.user):
            yield

    def test_ls_findings(self):
        finding = self.project.findings.first()
        result = self.backend.ls('/project/reporting/findings/')
        paths = [e['path'] for e in result.entries or []]
        assert any(p.endswith(f'/{finding.finding_id}.yaml') for p in paths)

    def test_lazy_file_loading(self):
        with mock.patch('sysreptor.ai.agents.project.format_finding_data') as format_finding:
            self.backend.ls('/project/reporting/findings/')
            self.backend.glob('*.yaml', path='/project/reporting/findings/')
            format_finding.assert_not_called()

    def test_ls_notes(self):
        note = self.project.notes.first()
        result = self.backend.ls('/project/notes/')
        paths = [e['path'] for e in result.entries or []]
        assert any(p.endswith(f'/{note.note_id}.yaml') for p in paths)

    def test_read_finding(self):
        finding = self.project.findings.first()
        result = self.backend.read(finding_path(finding.finding_id))
        assert result.error is None
        assert finding.title in result.file_data['content']

    def test_read_note(self):
        note = create_projectnotebookpage(project=self.project, title='Test Note', text='Note body content')
        result = self.backend.read(note_path(note.note_id))
        assert result.error is None
        assert note.title in result.file_data['content']
        assert 'Note body content' in result.file_data['content']

    def test_read_note_excalidraw(self):
        note = create_projectnotebookpage(
            project=self.project,
            title='Excalidraw Note',
            type=NoteType.EXCALIDRAW,
            excalidraw_data={'elements': [{'id': 'e1', 'type': 'rectangle', 'x': 0, 'y': 0}]},
        )
        result = self.backend.read(note_path(note.note_id))
        assert result.error is None
        assert 'excalidraw_data' in result.file_data['content']
        assert 'Note body content' not in result.file_data['content']

    def test_read_not_found(self):
        result = self.backend.read('/project/reporting/findings/nonexistent.yaml')
        assert result.error is not None
        assert result.error.lower() in ['file_not_found', 'not found']

    def test_grep(self):
        finding = self.project.findings.first()
        result = self.backend.grep(finding.title, path='/project/reporting/findings/')
        assert any(m['path'].endswith(f'/{finding.finding_id}.yaml') for m in (result.matches or []))

    def test_grep_notes(self):
        note = create_projectnotebookpage(project=self.project, title='Unique grep note title', text='grep note body')
        result = self.backend.grep('Unique grep note title', path='/project/notes/')
        assert any(m['path'].endswith(f'/{note.note_id}.yaml') for m in (result.matches or []))

    def test_glob(self):
        finding = self.project.findings.first()
        result = self.backend.glob('*.yaml', path='/project/reporting/findings/')
        paths = [m['path'] for m in (result.matches or [])]
        assert any(p.endswith(f'/{finding.finding_id}.yaml') for p in paths)

    def test_glob_notes(self):
        note = self.project.notes.first()
        result = self.backend.glob('*.yaml', path='/project/notes/')
        paths = [m['path'] for m in (result.matches or [])]
        assert any(p.endswith(f'/{note.note_id}.yaml') for p in paths)

    def test_read_only_write(self):
        result = self.backend.write('/project/reporting/findings/new.yaml', 'content')
        assert result.error is not None
        assert 'read-only' in result.error.lower()
        assert 'update_field_value' in result.error
        # The routed backend sees the prefix-stripped path
        assert '/reporting/findings/new.yaml' in result.error

    def test_read_only_edit(self):
        finding = self.project.findings.first()
        result = self.backend.edit(finding_path(finding.finding_id), 'old', 'new')
        assert result.error is not None
        assert 'read-only' in result.error.lower()

    def test_project_scoping(self):
        other_project = create_project(members=[self.user])
        other_finding = other_project.findings.first()
        result = self.backend.read(finding_path(other_finding.finding_id))
        assert result.error is not None


@pytest.mark.django_db()
class TestProjectFilesystemAgent:
    def test_agent_read_file_flow(self):
        user = create_user()
        project = create_project(members=[user])
        client = api_client(user=user)
        finding = project.findings.first()
        file_path = finding_path(finding.finding_id)
        llm_messages = [
            AIMessage(content='', tool_calls=[
                ToolCall(id='tool_call_1', name='read_file', args={'file_path': file_path}),
            ]),
            AIMessage(content=f'The finding title is {finding.title}.'),
        ]
        with mock_llm_response(messages=llm_messages):
            res = client.post(reverse('chatthread-list'), data={
                'agent': 'project_ask',
                'project': project.id,
                'messages': ['What is the finding title?'],
                'context': {},
            })
            assert res.status_code == 200
            events = parse_sse_events(res)
            tool_status = next(e for e in events if e['type'] == 'tool_call_status')
            assert tool_status['content']['name'] == 'read_file'
            assert tool_status['content']['status'] == 'success'
            assert finding.title in tool_status['content']['content']

    def test_agent_scratch_file_write_then_read(self):
        # Regular (non-/project) files use the read-write StateBackend.
        user = create_user()
        project = create_project(members=[user])
        client = api_client(user=user)
        llm_messages = [
            AIMessage(content='', tool_calls=[
                ToolCall(id='tool_call_1', name='write_file', args={'file_path': '/scratch/plan.md', 'content': 'step 1: investigate'}),
            ]),
            AIMessage(content='', tool_calls=[
                ToolCall(id='tool_call_2', name='read_file', args={'file_path': '/scratch/plan.md'}),
            ]),
            AIMessage(content='Saved and read back the plan.'),
        ]
        with mock_llm_response(messages=llm_messages):
            res = client.post(reverse('chatthread-list'), data={
                'agent': 'project_agent',
                'project': project.id,
                'messages': ['Write a plan to a scratch file and read it back'],
                'context': {},
            })
            assert res.status_code == 200
            events = parse_sse_events(res)
            statuses = [e for e in events if e['type'] == 'tool_call_status']
            write_status = next(e for e in statuses if e['content']['name'] == 'write_file')
            assert write_status['content']['status'] == 'success'
            read_status = next(e for e in statuses if e['content']['name'] == 'read_file')
            assert read_status['content']['status'] == 'success'
            assert 'step 1: investigate' in read_status['content']['content']

    def test_agent_write_project_path_read_only(self):
        # Writing into /project/ via the generic write tool is rejected with a helpful error.
        user = create_user()
        project = create_project(members=[user])
        client = api_client(user=user)
        finding = project.findings.first()
        llm_messages = [
            AIMessage(content='', tool_calls=[
                ToolCall(id='tool_call_1', name='write_file', args={'file_path': finding_path(finding.finding_id), 'content': 'hacked'}),
            ]),
            AIMessage(content='I cannot write there.'),
        ]
        with mock_llm_response(messages=llm_messages):
            res = client.post(reverse('chatthread-list'), data={
                'agent': 'project_agent',
                'project': project.id,
                'messages': ['Overwrite the finding file'],
                'context': {},
            })
            assert res.status_code == 200
            events = parse_sse_events(res)
            tool_status = next(e for e in events if e['type'] == 'tool_call_status')
            assert tool_status['content']['name'] == 'write_file'
            assert tool_status['content']['status'] == 'error'
            assert 'update_field_value' in tool_status['content']['content']


DEMO_SKILL_MD = textwrap.dedent("""\
    ---
    name: demo-skill
    description: Use when writing demo finding summaries from notes.
    ---

    # Demo skill

    Always start findings with a one-line summary.
    """).strip()


def create_skills_note_tree(project, skills: dict | None = None):
    agents = create_projectnotebookpage(project=project, title='.agents', parent=None, order=1, text='', checked=None)
    skills_root = create_projectnotebookpage(project=project, title='skills', parent=agents, order=1, text='', checked=None)

    def build(parent, tree):
        for order, (name, value) in enumerate(tree.items(), start=1):
            note = create_projectnotebookpage(
                project=project, title=name, parent=parent, order=order,
                text=value if isinstance(value, str) else '', checked=None,
            )
            if isinstance(value, dict):
                build(note, value)

    build(skills_root, skills or {})
    return skills_root


def create_nested_agents_skill(project):
    parent = create_projectnotebookpage(project=project, title='Other', parent=None, order=1, text='', checked=None)
    agents = create_projectnotebookpage(project=project, title='.agents', parent=parent, order=1, text='', checked=None)
    skills_root = create_projectnotebookpage(project=project, title='skills', parent=agents, order=1, text='', checked=None)
    skill_dir = create_projectnotebookpage(project=project, title='nested-skill', parent=skills_root, order=1, text='', checked=None)
    create_projectnotebookpage(project=project, title='SKILL.md', parent=skill_dir, order=1, text=DEMO_SKILL_MD, checked=None)


def create_agents_md_only(project):
    agents = create_projectnotebookpage(project=project, title='.agents', parent=None, order=1, text='', checked=None)
    create_projectnotebookpage(project=project, title='AGENTS.md', parent=agents, order=1, text='Prefer short titles.', checked=None)


def get_agent_system_prompt(project, user):
    """Run a chat request and return the system prompt handed to the model."""
    model = FakeChatModel(messages=iter([AIMessage(content='ok')]))
    with mock_llm_response(model=model):
        res = api_client(user=user).post(reverse('chatthread-list'), data={
            'agent': 'project_ask',
            'project': project.id,
            'messages': ['Hello'],
            'context': {},
        })
        assert res.status_code == 200
        parse_sse_events(res)
    system = model.message_log[0]['messages'][0]
    assert system.type == 'system'
    return system.content if isinstance(system.content, str) else str(system.content)


@pytest.mark.parametrize(('title', 'expected'), [
    ('my-skill', 'my-skill'),
    ('  foo  bar  ', 'foo bar'),
    ('a/b\\c', 'abc'),
    ('file<>:"|?*name', 'filename'),
    ('trailing.', 'trailing'),
    ('...', ''),
    ('', ''),
    (None, ''),
    ('café/test', 'cafétest'),
])
def test_normalize_note_filename(title, expected):
    assert NotesAgentsDirBackend.normalize_note_filename(title) == expected


@pytest.mark.django_db()
class TestNotesAgentsDirBackend:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user()
        self.project = create_project(members=[self.user], notes_kwargs=[])
        self.backend = CompositeBackend(
            default=StateBackend(),
            routes={
                ProjectFilesystemBackend.PROJECT_ROOT: ProjectFilesystemBackend(),
                NotesAgentsDirBackend.AGENTS_ROOT: NotesAgentsDirBackend(),
            },
        )
        with project_filesystem_runtime(self.project, self.user):
            yield

    @pytest.mark.parametrize(('setup', 'ls_path', 'expected_dirs'), [
        (lambda p: None, '/.agents/', []),
        (lambda p: None, '/.agents/skills/', []),
        (create_agents_md_only, '/.agents/skills/', []),
        (create_nested_agents_skill, '/.agents/', []),
        (lambda p: create_skills_note_tree(p, {'incomplete': {'readme.md': 'no skill md'}}),
         '/.agents/skills/', ['/.agents/skills/incomplete/']),
        (lambda p: create_skills_note_tree(p, {'my/skill': {'SKILL.md': DEMO_SKILL_MD}}),
         '/.agents/skills/', ['/.agents/skills/myskill/']),
        (lambda p: create_skills_note_tree(p, {
                'demo-skill': {'SKILL.md': DEMO_SKILL_MD},
                'bad-skill': {'SKILL.md': 'not valid frontmatter'},  # present in FS; SkillsMiddleware skips parse failures
            }),
         '/.agents/skills/',
         ['/.agents/skills/bad-skill/', '/.agents/skills/demo-skill/'],
        ),
    ])
    def test_ls_lists_expected_dirs(self, setup, ls_path, expected_dirs):
        setup(self.project)
        result = self.backend.ls(ls_path)
        assert result.error is None
        dir_paths = sorted(e['path'] for e in (result.entries or []) if e.get('is_dir'))
        assert dir_paths == sorted(expected_dirs)

    def test_ls_and_read_non_skill_agents_content(self):
        agents = create_projectnotebookpage(project=self.project, title='.agents', parent=None, order=1, text='', checked=None)
        create_projectnotebookpage(project=self.project, title='instructions.md', parent=agents, order=1, text='# Hello agents', checked=None)
        skills_root = create_projectnotebookpage(project=self.project, title='skills', parent=agents, order=2, text='', checked=None)
        skill_dir = create_projectnotebookpage(project=self.project, title='demo-skill', parent=skills_root, order=1, text='', checked=None)
        create_projectnotebookpage(project=self.project, title='SKILL.md', parent=skill_dir, order=1, text=DEMO_SKILL_MD, checked=None)

        root_paths = [e['path'] for e in (self.backend.ls('/.agents/').entries or [])]
        assert '/.agents/instructions.md' in root_paths
        assert '/.agents/skills/' in root_paths

        read = self.backend.read('/.agents/instructions.md')
        assert read.error is None
        assert 'Hello agents' in read.file_data['content']

    def test_ls_and_read_skill(self):
        create_skills_note_tree(self.project, {
            'demo-skill': {
                'SKILL.md': DEMO_SKILL_MD,
                'references.md': '# Refs\nMore detail.',
                'references': {'api.md': '# API\nNested docs.'},
            },
        })
        assert '/.agents/skills/demo-skill/' in [e['path'] for e in (self.backend.ls('/.agents/skills/').entries or [])]

        skill_paths = [e['path'] for e in (self.backend.ls('/.agents/skills/demo-skill/').entries or [])]
        assert '/.agents/skills/demo-skill/SKILL.md' in skill_paths
        assert '/.agents/skills/demo-skill/references.md' in skill_paths
        assert '/.agents/skills/demo-skill/references/' in skill_paths  # nested dir

        nested_paths = [e['path'] for e in (self.backend.ls('/.agents/skills/demo-skill/references/').entries or [])]
        assert '/.agents/skills/demo-skill/references/api.md' in nested_paths

        for path, expected in [
            ('/.agents/skills/demo-skill/SKILL.md', 'Always start findings'),
            ('/.agents/skills/demo-skill/references.md', 'More detail.'),
            ('/.agents/skills/demo-skill/references/api.md', 'Nested docs.'),
        ]:
            read = self.backend.read(path)
            assert read.error is None
            assert expected in read.file_data['content']

    def test_download_files(self):
        create_skills_note_tree(self.project, {'demo-skill': {'SKILL.md': DEMO_SKILL_MD}})
        responses = self.backend.download_files(['/.agents/skills/demo-skill/SKILL.md', '/.agents/skills/missing/SKILL.md'])
        assert responses[0].error is None
        assert b'name: demo-skill' in responses[0].content
        assert responses[1].error == 'file_not_found'

    def test_ls_empty_directory(self):
        # A note whose only children are non-text (e.g. excalidraw) is an empty directory.
        create_skills_note_tree(self.project, {'demo-skill': {'SKILL.md': DEMO_SKILL_MD}})
        skill_dir = self.project.notes.get(title='demo-skill')
        empty_dir = create_projectnotebookpage(project=self.project, title='empty', parent=skill_dir, order=2, text='', checked=None)
        create_projectnotebookpage(project=self.project, title='diagram', parent=empty_dir, type=NoteType.EXCALIDRAW, order=1, checked=None)

        result = self.backend.ls('/.agents/skills/demo-skill/empty/')
        assert result.error is None
        assert result.entries == []

        assert self.backend.ls('/.agents/skills/demo-skill/missing/').error == 'file_not_found'

    def test_duplicate_titles_pick_highest_order(self):
        skills_root = create_skills_note_tree(self.project, {'demo-skill': {'SKILL.md': DEMO_SKILL_MD}})
        second = create_projectnotebookpage(project=self.project, title='demo-skill', parent=skills_root, order=99, text='', checked=None)
        create_projectnotebookpage(
            project=self.project, title='SKILL.md', parent=second, order=1,
            text='---\nname: other\ndescription: last wins\n---\n# Other\n', checked=None,
        )
        read = self.backend.read('/.agents/skills/demo-skill/SKILL.md')
        assert read.error is None
        assert 'last wins' in read.file_data['content']
        assert 'name: demo-skill' not in read.file_data['content']

    def test_read_only_write(self):
        create_skills_note_tree(self.project, {'demo-skill': {'SKILL.md': DEMO_SKILL_MD}})
        result = self.backend.write('/.agents/skills/demo-skill/SKILL.md', 'hacked')
        assert result.error is not None
        assert 'read-only' in result.error.lower()

    def test_download_agents_md(self):
        agents = create_projectnotebookpage(project=self.project, title='.agents', parent=None, order=1, text='', checked=None)
        create_projectnotebookpage(
            project=self.project, title='AGENTS.md', parent=agents, order=1,
            text='# Project memory\nPrefer short finding titles.', checked=None,
        )
        responses = self.backend.download_files(['/.agents/AGENTS.md', '/.agents/missing.md'])
        assert responses[0].error is None
        assert b'Prefer short finding titles' in responses[0].content
        assert responses[1].error == 'file_not_found'

    def test_grep_and_glob(self):
        create_skills_note_tree(self.project, {'demo-skill': {'SKILL.md': DEMO_SKILL_MD}})
        grep = self.backend.grep('Always start findings', path='/.agents/skills/')
        assert any(m['path'].endswith('/SKILL.md') for m in (grep.matches or []))
        glob = self.backend.glob('**/SKILL.md', path='/.agents/skills/')
        assert any(m['path'].endswith('/demo-skill/SKILL.md') for m in (glob.matches or []))


@pytest.mark.django_db()
class TestNotesAgentDirAgent:
    @pytest.mark.parametrize('with_skill', [
        True,
        False,
    ])
    def test_skills_catalog_in_system_prompt(self, with_skill):
        user = create_user()
        project = create_project(members=[user], notes_kwargs=[])
        if with_skill:
            create_skills_note_tree(project, {'demo-skill': {'SKILL.md': DEMO_SKILL_MD}})

        content = get_agent_system_prompt(project, user)
        skill_markers = ['demo-skill', 'writing demo finding summaries', '/.agents/skills/demo-skill/SKILL.md']
        if with_skill:
            assert all(marker in content for marker in skill_markers)
        else:
            assert not any(marker in content for marker in skill_markers)
            assert 'Cannot load skills' not in content
            assert 'Skills load errors' not in content

    def test_agent_read_skill_file(self):
        user = create_user()
        project = create_project(members=[user], notes_kwargs=[])
        create_skills_note_tree(project, {'demo-skill': {'SKILL.md': DEMO_SKILL_MD}})
        client = api_client(user=user)
        llm_messages = [
            AIMessage(content='', tool_calls=[
                ToolCall(id='tool_call_1', name='read_file', args={'file_path': '/.agents/skills/demo-skill/SKILL.md', 'limit': 1000}),
            ]),
            AIMessage(content='Loaded the demo skill.'),
        ]
        with mock_llm_response(messages=llm_messages):
            res = client.post(reverse('chatthread-list'), data={
                'agent': 'project_ask',
                'project': project.id,
                'messages': ['Load the demo skill'],
                'context': {},
            })
            assert res.status_code == 200
            events = parse_sse_events(res)
            tool_status = next(e for e in events if e['type'] == 'tool_call_status')
            assert tool_status['content']['name'] == 'read_file'
            assert tool_status['content']['status'] == 'success'
            assert 'Always start findings' in tool_status['content']['content']

    @pytest.mark.parametrize('with_agents_md', [True, False])
    def test_agents_md_in_system_prompt(self, with_agents_md):
        user = create_user()
        project = create_project(members=[user], notes_kwargs=[])
        memory_text = 'Prefer short finding titles for this engagement.'
        if with_agents_md:
            agents = create_projectnotebookpage(project=project, title='.agents', parent=None, order=1, text='', checked=None)
            create_projectnotebookpage(project=project, title='AGENTS.md', parent=agents, order=1, text=memory_text, checked=None)

        content = get_agent_system_prompt(project, user)
        if with_agents_md:
            assert '/.agents/AGENTS.md' in content
            assert memory_text in content
        else:
            assert memory_text not in content
            assert '(No memory loaded)' in content



@pytest.mark.django_db()
class TestDjangoModelCheckpointer:
    def setup_method(self):
        self.thread = ChatThread.objects.create(
            user=create_user(),
            project=create_project(),
        )
        self.saver = DjangoModelCheckpointer()

    def _config(self, checkpoint_id=None, checkpoint_ns=''):
        configurable = {
            'thread_id': str(self.thread.id),
            'checkpoint_ns': checkpoint_ns,
        }
        if checkpoint_id is not None:
            configurable['checkpoint_id'] = str(checkpoint_id)
        return {'configurable': configurable}

    def test_put_get_roundtrip_splits_blobs(self):
        checkpoint_id = str(uuid4())
        version = self.saver.get_next_version(None, None)
        checkpoint = {
            'v': 4,
            'id': checkpoint_id,
            'ts': '2026-01-01T00:00:00+00:00',
            'channel_values': {
                'messages': [{'role': 'user', 'content': 'hi'}],
                'count': 1,
            },
            'channel_versions': {
                'messages': version,
                'count': version,
            },
            'versions_seen': {},
        }
        config = self._config()
        saved = self.saver.put(config, checkpoint, {'source': 'input', 'step': 1, 'writes': {}}, {
            'messages': version,
            'count': version,
        })
        assert saved['configurable']['checkpoint_id'] == checkpoint_id

        assert LangchainCheckpointBlob.objects.filter(
            thread=self.thread,
            channel='messages',
            version=version,
        ).exists()
        assert not LangchainCheckpointBlob.objects.filter(
            thread=self.thread,
            channel='count',
        ).exists()

        loaded = self.saver.get_tuple(self._config(checkpoint_id=checkpoint_id))
        assert loaded is not None
        assert loaded.checkpoint['channel_values']['messages'] == [{'role': 'user', 'content': 'hi'}]
        assert loaded.checkpoint['channel_values']['count'] == 1
        # Slimmed JSON keeps only inline primitives
        row = LangchainCheckpoint.objects.get(thread=self.thread, checkpoint_id=checkpoint_id)
        assert 'messages' not in (row.checkpoint.get('channel_values') or {})
        assert row.checkpoint['channel_values']['count'] == 1

    def test_put_writes_write_once_and_special_upsert(self):
        checkpoint_id = uuid4()
        LangchainCheckpoint.objects.create(
            thread=self.thread,
            checkpoint_id=checkpoint_id,
            checkpoint={'id': str(checkpoint_id), 'channel_versions': {}, 'channel_values': {}},
        )
        config = self._config(checkpoint_id=checkpoint_id)

        self.saver.put_writes(config, [('messages', 'a')], task_id='t1')
        self.saver.put_writes(config, [('messages', 'b')], task_id='t1')
        writes = list(LangchainCheckpointWrite.objects.filter(thread=self.thread, checkpoint_id=checkpoint_id))
        assert len(writes) == 1
        assert self.saver.serde.loads_typed((writes[0].type, writes[0].blob)) == 'a'

        # Special channels in WRITES_IDX_MAP are upserted
        special = next(iter(WRITES_IDX_MAP))
        self.saver.put_writes(config, [(special, 'one')], task_id='t2')
        self.saver.put_writes(config, [(special, 'two')], task_id='t2')
        special_writes = list(LangchainCheckpointWrite.objects.filter(
            thread=self.thread,
            checkpoint_id=checkpoint_id,
            task_id='t2',
            channel=special,
        ))
        assert len(special_writes) == 1
        assert self.saver.serde.loads_typed((special_writes[0].type, special_writes[0].blob)) == 'two'

        loaded = self.saver.get_tuple(config)
        assert loaded is not None
        assert ('t1', 'messages', 'a') in loaded.pending_writes
        assert ('t2', special, 'two') in loaded.pending_writes

    def test_delta_channel_history_seed_and_writes(self):
        parent_id = uuid4()
        head_id = uuid4()
        version = self.saver.get_next_version(None, None)

        parent_checkpoint = {
            'v': 4,
            'id': str(parent_id),
            'ts': '2026-01-01T00:00:00+00:00',
            'channel_values': {'messages': [{'id': 1}]},
            'channel_versions': {'messages': version},
            'versions_seen': {},
        }
        self.saver.put(self._config(), parent_checkpoint, {'source': 'loop', 'step': 0, 'writes': {}}, {
            'messages': version,
        })
        self.saver.put_writes(self._config(checkpoint_id=parent_id), [('messages', {'id': 2})], task_id='w1')

        LangchainCheckpoint.objects.create(
            thread=self.thread,
            checkpoint_id=head_id,
            parent_checkpoint_id=parent_id,
            checkpoint={
                'v': 4,
                'id': str(head_id),
                'ts': '2026-01-01T00:00:01+00:00',
                'channel_values': {},
                'channel_versions': {'messages': version},
                'versions_seen': {},
            },
        )

        history = self.saver.get_delta_channel_history(
            config=self._config(checkpoint_id=head_id),
            channels=['messages'],
        )
        assert 'seed' in history['messages']
        assert history['messages']['seed'] == [{'id': 1}]
        assert history['messages']['writes'] == [('w1', 'messages', {'id': 2})]
