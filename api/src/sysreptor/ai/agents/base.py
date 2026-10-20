import json
import logging
from typing import Any

import yaml
from decouple import config
from deepagents._tools import _apply_tool_description_overrides
from deepagents.backends import StateBackend
from deepagents.middleware.patch_tool_calls import PatchToolCallsMiddleware
from deepagents.middleware.subagents import GENERAL_PURPOSE_SUBAGENT
from deepagents.middleware.summarization import create_summarization_middleware
from deepagents.profiles import GeneralPurposeSubagentProfile
from deepagents.profiles.harness.harness_profiles import (
    _apply_profile_prompt,
    _harness_profile_for_model,
)
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from langchain import chat_models
from langchain.agents import create_agent
from langchain.agents.middleware import (
    ModelRetryMiddleware,
    TodoListMiddleware,
    ToolErrorMiddleware,
)
from langchain.messages import AIMessage, AIMessageChunk, AnyMessage, HumanMessage, ToolMessage
from langchain_core._api import suppress_langchain_beta_warning
from langchain_core.exceptions import LangChainException
from langgraph.config import get_config
from langgraph.stream import UpdatesTransformer
from rest_framework.exceptions import ValidationError as DRFValidationError

from sysreptor.ai.agents.checkpointer import DjangoModelCheckpointer
from sysreptor.ai.agents.middleware import (
    CustomSubagentMiddleware,
    MergeConsecutiveMessagesMiddleware,
    MessageTimestampMiddleware,
    SelectConfiguredModelMiddleware,
    stamp_message_timestamp,
    subagent_checkpoint_ns,
)
from sysreptor.ai.models import AgentRunStatus, ChatThread, LangchainCheckpoint
from sysreptor.utils.configuration import configuration
from sysreptor.utils.history import history_context
from sysreptor.utils.utils import copy_keys, omit_keys


def format_agent_error(ex: Exception, generic_msg: str | None = 'Error: Internal server error') -> str:
    if isinstance(ex, ObjectDoesNotExist):
        return 'Error: Object not found'
    elif isinstance(ex, ValidationError | DRFValidationError):
        return f'Error: {ex}'
    elif isinstance(ex, LangChainException):
        body = getattr(ex, 'body', None)
        if isinstance(body, dict) and isinstance(body.get('message'), str):
            return f'Error: {body["message"]}'
        if getattr(ex, 'message', None):
            return f'Error: {ex.message}'
    return generic_msg


def to_yaml(data: Any) -> str:
    data_json = json.loads(json.dumps(data, cls=DjangoJSONEncoder))
    out = '\n' + yaml.dump(data_json, allow_unicode=True)
    if not out.endswith('\n'):
        out += '\n'
    return out


def to_short_string(s) -> str:
    """
    Encode a string to a short representation suitable for LLM prompts.
    """
    if isinstance(s, None | int | float | bool):
        return json.dumps(s)

    enc = json.dumps(str(s))
    if s and s == enc[1:-1] and not any(c in s for c in [' ']):
        return s
    return enc


def to_inline_context(data: dict[str, Any]) -> str:
    return ' '.join(f'{to_short_string(k)}={to_short_string(v)}' for k, v in data.items())


def is_in_subagent() -> bool:
    try:
        config = get_config()
        ns = (config or {}).get('configurable') or {}
        checkpoint_ns = ns.get('checkpoint_ns')
        return bool(checkpoint_ns)
    except RuntimeError:
        return False


def get_model_configs(*, include_hidden: bool = True) -> list:
    try:
        out = [json.loads(c) for c in configuration.AI_AGENT_MODELS or []]
    except Exception:
        out = []

    if not out and (legacy_ai_model := config('AI_AGENT_MODEL', default=None)):
        provider, model_name = legacy_ai_model.split(':', 1)
        env_prefix = {'mistralai': 'mistral'}.get(provider, provider).upper()
        out = [{
            'id': model_name,
            'model': model_name,
            'provider': provider,
            'api_key': config(f'{env_prefix}_API_KEY', default=None),
            'base_url': config(f'{env_prefix}_BASE_URL', default=config(f'{env_prefix}_API_BASE', default=config(f'{env_prefix}_HOST', default=None))),
        }]

    if not include_hidden:
        out = [c for c in out if not c.get('hidden')]
    return out


def get_default_model_id() -> str:
    default_model = next(iter(get_model_configs(include_hidden=False)), None)
    if not default_model:
        raise ValueError('No LLM model configured')
    return default_model.get('id')


def init_chat_model(model: str):
    config = next(filter(lambda c: c.get('id') == model, get_model_configs()), None)
    if not config:
        raise ValueError(f'Unknown model: {model}')
    return chat_models.init_chat_model(
        model=config.get('model'),
        model_provider=config.get('provider', 'deepseek'),
        **omit_keys(config, ['id', 'label', 'provider', 'model', 'vision_model', 'hidden']),
    )


def create_sysreptor_agent(system_prompt: str, tools: list, middleware: list, **kwargs):
    """
    Create a SysReptor agent.
    Based on langchain deepagents library.
    """
    default_model = init_chat_model(get_default_model_id())
    profile = _harness_profile_for_model(default_model, spec=None)
    tools = _apply_tool_description_overrides(tools, profile.tool_description_overrides)
    subagent_tools = [
        t for t in tools
        if (getattr(t, 'metadata', None) or {}).get('subagent', True)
    ]

    backend = StateBackend()
    middleware = [
        SelectConfiguredModelMiddleware(),
        TodoListMiddleware(),
        PatchToolCallsMiddleware(),
        create_summarization_middleware(model=default_model, backend=backend),
        MessageTimestampMiddleware(),
        ModelRetryMiddleware(max_retries=2, on_failure='error'),
        ToolErrorMiddleware(on_error=lambda ex, request: format_agent_error(ex)),
    ] + profile.materialize_extra_middleware() + middleware + [
        MergeConsecutiveMessagesMiddleware(),
    ]

    gp_profile = profile.general_purpose_subagent or GeneralPurposeSubagentProfile()
    if gp_profile.system_prompt is not None:
        subagent_prompt = gp_profile.system_prompt
        if profile.system_prompt_suffix is not None:
            subagent_prompt += '\n\n' + profile.system_prompt_suffix
    else:
        subagent_prompt = _apply_profile_prompt(profile, GENERAL_PURPOSE_SUBAGENT['system_prompt'])
    subagents = [
        GENERAL_PURPOSE_SUBAGENT | {
            'description': gp_profile.description or GENERAL_PURPOSE_SUBAGENT['description'],
            'system_prompt': subagent_prompt,
            'model': default_model,
            'tools': subagent_tools,
            'middleware': middleware,
        },
    ]
    agent = create_agent(
        model=default_model,
        system_prompt=system_prompt + '\n\n' + _apply_profile_prompt(profile, ''),
        tools=tools,
        middleware=middleware + [
            CustomSubagentMiddleware(backend=backend, subagents=subagents),
        ],
        checkpointer=DjangoModelCheckpointer(),
        **kwargs,
    ).with_config({"recursion_limit": 1000})
    return agent


def format_message(m: AnyMessage) -> dict|None:
    if isinstance(m, HumanMessage | AIMessage) and not m.additional_kwargs.get('injected_context'):
        content = ''
        reasoning_content = ''
        for block in m.content_blocks:
            if isinstance(block, dict):
                # Only extract text blocks, skip tool_use blocks
                match block.get('type'):
                    case 'text':
                        content += block.get('text', '')
                    case 'reasoning':
                        reasoning_content += block.get('reasoning', '')
        if content or reasoning_content:
            return {
                'id': m.id,
                'role': 'assistant' if isinstance(m, AIMessage) else 'user',
                'timestamp': m.additional_kwargs.get('timestamp'),
                **({'text': content} if content else {}),
                **({'reasoning': reasoning_content} if reasoning_content else {}),
            }
    elif isinstance(m, ToolMessage):
        return {
            'id': m.tool_call_id,
            'role': 'tool',
            'timestamp': m.additional_kwargs.get('timestamp'),
            'tool_call': {
                'id': m.tool_call_id,
                'name': m.name,
                'status': m.status,
                'timestamp': m.additional_kwargs.get('timestamp'),
                'output': m.additional_kwargs.get('output') or ({'message': m.content} if m.name in ['task'] else {}),
            },
        }
    return None


def user_message_event(input) -> dict | None:
    msg = (input.get('messages') or [None])[0] if isinstance(input, dict) else None
    if isinstance(msg, HumanMessage):
        stamp_message_timestamp(msg)
        if formatted := format_message(msg):
            return {'type': 'text', 'content': {**formatted, 'replace': True}}
    return None


async def agent_stream(agent, input, thread: ChatThread, context: dict[str, str]|None = None, model: str | None = None, **kwargs):
    try:
        if event := user_message_event(input):
            yield event

        with history_context(history_user=thread.user, set_history_date=False):
            pending_tool_call_ids = []
            namespace_to_tool_call_id = {}
            message_id_by_run: dict[str, str] = {}
            with suppress_langchain_beta_warning():
                stream = await agent.astream_events(
                    input,
                    config={
                        'configurable': {
                            'thread_id': str(thread.id),
                        },
                    },
                    context=agent.context_schema(**(context or {}) | {
                        'user_id': thread.user_id,
                        'project_id': thread.project_id,
                        'model': model or get_default_model_id(),
                    }),
                    durability='async',
                    version='v3',
                    transformers=[UpdatesTransformer],
                    **kwargs,
                )
                async for event in stream:
                    method = event['method']
                    namespace = event['params']['namespace']
                    chunk = event['params']['data']

                    # Map subagent namespace to tool call id
                    # https://github.com/langchain-ai/langgraph/issues/6714
                    meta = {
                        'subagent': None,
                    }
                    if namespace and (src := namespace[0] if isinstance(namespace[0], str) else str(namespace[0])):
                        root_ns = src.split('|', 1)[0]
                        if root_ns.startswith('subagent:') and root_ns.count(':') >= 2:
                            parsed_id = root_ns.split(':', 2)[2]
                            namespace_to_tool_call_id.setdefault(src, parsed_id)
                            if parsed_id in pending_tool_call_ids:
                                pending_tool_call_ids.remove(parsed_id)
                        elif src not in namespace_to_tool_call_id and pending_tool_call_ids:
                            namespace_to_tool_call_id[src] = pending_tool_call_ids.pop(0)
                        meta['subagent'] = namespace_to_tool_call_id.get(src)

                    # Stream messages and tool calls
                    if method == 'messages' and isinstance(chunk, tuple) and len(chunk) == 2:
                        payload, msg_metadata = chunk
                        run_id = str((msg_metadata if isinstance(msg_metadata, dict) else {}).get('run_id', ''))
                        if isinstance(payload, dict) and payload.get('event') == 'message-start':
                            if payload.get('role') != 'tool' and run_id and (msg_id := payload.get('id') or payload.get('message_id')):
                                message_id_by_run[run_id] = msg_id
                        elif isinstance(payload, dict) and payload.get('event') == 'content-block-delta' and (msg_id := message_id_by_run.get(run_id)):
                            delta = payload.get('delta') or {}
                            if delta.get('type') == 'text-delta' and 'text' in delta:
                                yield {'type': 'text', 'content': {'id': msg_id, 'role': 'assistant', 'text': delta['text']}, **meta}
                            elif delta.get('type') == 'reasoning-delta' and 'reasoning' in delta:
                                yield {'type': 'text', 'content': {'id': msg_id, 'role': 'assistant', 'reasoning': delta['reasoning']}, **meta}
                        elif isinstance(payload, AIMessage) and not isinstance(payload, AIMessageChunk) and (m := format_message(payload)):
                            yield {'type': 'text', 'content': {**m, 'replace': True}, **meta}
                    elif method == 'updates' and isinstance(chunk, dict) and (raw_interrupt := chunk.get('__interrupt__')):
                        interrupts = raw_interrupt if isinstance(raw_interrupt, list | tuple) else (raw_interrupt,)
                        yield {
                            'type': 'interrupt',
                            'content': [{'id': i.id, 'value': i.value} for i in interrupts],
                        }
                    elif method == 'updates' and isinstance(chunk, dict) and \
                        (messages := (chunk.get('model') or {}).get('messages')) and len(messages) >= 1 and isinstance(messages[0], AIMessage):
                        ai_message = messages[0]
                        stamp_message_timestamp(ai_message)
                        if formatted := format_message(ai_message):
                            yield {
                                'type': 'text',
                                'content': {
                                    **formatted,
                                    'timestamp': ai_message.additional_kwargs.get('timestamp') or timezone.now().isoformat(),
                                    'replace': True,
                                },
                                **meta,
                            }

                        for c in ai_message.tool_calls:
                            if not c.get('id'):
                                continue
                            if c.get('name') in ['task', 'analyze_image'] and isinstance(c.get('args'), dict):
                                pending_tool_call_ids.append(c['id'])
                            yield {
                                'type': 'tool_call',
                                'content': {
                                    'status': 'pending',
                                    'timestamp': ai_message.additional_kwargs.get('timestamp') or timezone.now().isoformat(),
                                    'output': None,
                                    **copy_keys(c, ['id', 'name', 'args']),
                                },
                                **meta,
                            }
                    elif method == 'updates' and isinstance(chunk, dict) and (messages := (chunk.get('tools') or {}).get('messages')):
                        for c in messages:
                            if isinstance(c, ToolMessage):
                                stamp_message_timestamp(c)
                                yield {
                                    'type': 'tool_call_status',
                                    'content': {
                                        'id': c.tool_call_id,
                                        'name': c.name,
                                        'status': c.status,
                                        **copy_keys(c.additional_kwargs or {}, ['timestamp', 'output']),
                                    },
                                    **meta,
                                }
    except Exception as ex:
        logging.exception(ex)
        msg = format_agent_error(ex)
        yield {
            'type': 'error',
            'content': msg,
        }
        raise ex


def covered_keys_from_messages(messages: list) -> list[str]:
    """Buffer keys (text:{id} / tool_call:{id}) already present in a history snapshot."""
    covered = set()
    for m in messages:
        if isinstance(m, HumanMessage | AIMessage) and m.id:
            covered.add(f'text:{m.id}')
        elif isinstance(m, ToolMessage) and m.tool_call_id and m.status != 'pending':
            covered.add(f'tool_call:{m.tool_call_id}')
    return list(covered)


def format_history_messages(raw_messages: list, pending_status='error') -> list[dict]:
    messages = []
    tool_calls = []
    finished_tool_calls = {m.tool_call_id for m in raw_messages if isinstance(m, ToolMessage) and m.tool_call_id}
    for m in raw_messages:
        if isinstance(m, AIMessage):
            for tc in m.tool_calls:
                tool_calls.append(copy_keys(tc, ['id', 'name', 'args']))

        formatted = format_message(m)
        if formatted:
            if isinstance(m, ToolMessage):
                existing_tc = next((tc for tc in tool_calls if tc['id'] == m.tool_call_id), None)
                formatted['tool_call'].update({
                    'args': existing_tc['args'] if existing_tc else {},
                })
            messages.append(formatted)

        # Emit pending/incomplete tool calls that have no ToolMessage yet
        if isinstance(m, AIMessage):
            for tc in m.tool_calls:
                tid = tc.get('id')
                if not tid or tid in finished_tool_calls:
                    continue
                messages.append({
                    'id': tid,
                    'role': 'tool',
                    'timestamp': m.additional_kwargs.get('timestamp'),
                    'tool_call': {
                        'id': tid,
                        'name': tc.get('name'),
                        'args': tc.get('args') or {},
                        'status': pending_status,
                        'output': None,
                    },
                })
    return messages


def get_chat_history(agent, thread: ChatThread):
    thread_exists = LangchainCheckpoint.objects \
        .filter(thread=thread) \
        .exists()
    if not thread_exists:
        return {
            'id': thread.id,
            'project': thread.project_id,
            'messages': [],
            'interrupts': [],
            'covered': [],
        }

    state = agent.get_state(config={'configurable': {'thread_id': str(thread.id)}})
    raw_messages = state.values.get('messages', [])
    covered = set(covered_keys_from_messages(raw_messages))

    pending_status = 'pending' if thread.run_status in [AgentRunStatus.RUNNING, AgentRunStatus.INTERRUPTED] else 'error'
    messages = format_history_messages(raw_messages, pending_status=pending_status)

    # Nest task-tool subagent histories (deterministic checkpoint_ns; analyze_image is not hydrated).
    task_tools = [
        m for m in messages
        if m.get('role') == 'tool'
        and (m.get('tool_call') or {}).get('name') == 'task'
        and (m.get('tool_call') or {}).get('id')
    ]
    if task_tools:
        ns_by_tool_id = {
            tc['id']: subagent_checkpoint_ns((tc.get('args') or {}).get('subagent_type'), tc['id'])
            for m in task_tools
            if (tc := m['tool_call'])
        }
        namespaces_values = agent.checkpointer.get_values_by_namespaces(str(thread.id), list(ns_by_tool_id.values()))
        for m in task_tools:
            tc = m['tool_call']
            if raw_messages := namespaces_values.get(ns_by_tool_id[tc['id']], {}).get('messages'):
                tc['subagentMessages'] = format_history_messages(raw_messages, pending_status=pending_status)
                covered.update(covered_keys_from_messages(raw_messages))

    return {
        'id': thread.id,
        'project': thread.project_id,
        'messages': messages,
        'interrupts': [{'id': i.id, 'value': i.value} for i in state.interrupts],
        'covered': list(covered),
    }
