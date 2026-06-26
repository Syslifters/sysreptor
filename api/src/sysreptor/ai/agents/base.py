import asyncio
import json
import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

import yaml
from asgiref.sync import sync_to_async
from decouple import config
from deepagents._tools import _apply_tool_description_overrides
from deepagents.backends import StateBackend
from deepagents.graph import BASE_AGENT_PROMPT
from deepagents.middleware.patch_tool_calls import PatchToolCallsMiddleware
from deepagents.middleware.subagents import GENERAL_PURPOSE_SUBAGENT, SubAgentMiddleware
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
from langchain.agents.middleware import AgentMiddleware, AgentState, TodoListMiddleware
from langchain.messages import AIMessage, AnyMessage, HumanMessage, ToolMessage
from langchain.tools import ToolRuntime, tool
from langgraph.config import get_config
from langgraph.types import Command
from rest_framework.exceptions import ValidationError as DRFValidationError

from sysreptor.ai.agents.checkpointer import DjangoModelCheckpointer
from sysreptor.ai.agents.middleware import MergeConsecutiveMessagesMiddleware, SelectConfiguredModelMiddleware
from sysreptor.ai.models import ChatThread, LangchainCheckpoint
from sysreptor.utils.configuration import configuration
from sysreptor.utils.history import history_context
from sysreptor.utils.utils import copy_keys, omit_keys


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


def agent_tool(metadata=None, **kwargs):
    def decorator(func: Callable) -> Callable:
        if not asyncio.iscoroutinefunction(func):
            func = sync_to_async(func)

        @tool(**kwargs)
        @wraps(func)
        async def tool_func(*tool_args, runtime: ToolRuntime, **tool_kwargs):
            out = ToolMessage(
                content='',
                status='error',
                tool_call_id=runtime.tool_call_id,
            )

            try:
                res_output = None
                res_content = await func(*tool_args, runtime=runtime, **tool_kwargs)
                if isinstance(res_content, tuple):
                    res_content, res_output = res_content
                if not isinstance(res_content, str):
                    res_content = to_yaml(res_content)
                out.content = res_content
                out.additional_kwargs['output'] = res_output or {}
                out.status = 'success'
            except ObjectDoesNotExist:
                out.content = 'Error: Object not found'
            except (ValidationError, DRFValidationError) as ex:
                out.content = f'Error: {ex}'
            except Exception as ex:
                logging.exception(ex)
                out.content = 'Error: Unexpected error'
            stamp_message_timestamp(out)
            return Command(update={
                'messages': [out],
            })
        tool_func.metadata = (tool_func.metadata or {}) | (metadata or {})
        return tool_func
    return decorator


def is_in_subagent() -> bool:
    try:
        config = get_config()
        ns = (config or {}).get('configurable') or {}
        checkpoint_ns = ns.get('checkpoint_ns')
        return bool(checkpoint_ns)
    except RuntimeError:
        return False


def get_model_configs() -> list:
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

    return out


def get_default_model_id() -> str:
    default_model = next(iter(get_model_configs()), None)
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
        **omit_keys(config, ['id', 'label', 'provider', 'model']),
    )


def stamp_message_timestamp(message: HumanMessage | AIMessage | ToolMessage) -> None:
    if message.additional_kwargs.get('timestamp'):
        return
    message.additional_kwargs = {
        **(message.additional_kwargs or {}),
        'timestamp': timezone.now().isoformat(),
    }


class MessageTimestampMiddleware(AgentMiddleware[AgentState]):
    """
    Stamp completion timestamps on user and assistant messages for the chat UI.
    """

    async def abefore_agent(self, state, runtime):
        for m in reversed(state['messages']):
            if isinstance(m, HumanMessage):
                if not m.additional_kwargs.get('injected_context'):
                    stamp_message_timestamp(m)
                break

    async def aafter_model(self, state, runtime):
        for m in reversed(state['messages']):
            if isinstance(m, AIMessage):
                stamp_message_timestamp(m)
            else:
                break


def create_sysreptor_agent(system_prompt: str, tools: list, middleware: list, **kwargs):
    """
    Create a SysReptor agent.
    Based on langchain deepagents library.
    """
    default_model = init_chat_model(get_default_model_id())
    profile = _harness_profile_for_model(default_model, spec=None)
    tools = _apply_tool_description_overrides(tools, profile.tool_description_overrides)

    backend = StateBackend()
    middleware = [
        SelectConfiguredModelMiddleware(),
        TodoListMiddleware(),
        PatchToolCallsMiddleware(),
        create_summarization_middleware(model=default_model, backend=backend),
        MessageTimestampMiddleware(),
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
            'tools': tools,
            'middleware': middleware,
        },
    ]
    agent = create_agent(
        model=default_model,
        system_prompt=system_prompt + '\n\n' + _apply_profile_prompt(profile, BASE_AGENT_PROMPT),
        tools=tools,
        middleware=middleware + [
            SubAgentMiddleware(backend=backend, subagents=subagents),
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
                'content': m.content,
                **copy_keys(m.additional_kwargs or {}, ['timestamp', 'output']),
            },
        }
    return None


async def agent_stream(agent, thread: ChatThread, context: dict[str, str]|None = None, model: str | None = None, **kwargs):
    try:
        with history_context(history_user=thread.user, set_history_date=False):
            yield {'type': 'metadata', 'content': {'thread_id': str(thread.id)}}

            pending_tool_call_ids = []
            namespace_to_tool_call_id = {}
            async for namespace, stream_mode, chunk in agent.astream(
                stream_mode=["messages", "values", "updates"],
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
                durability='exit',
                subgraphs=True,
                **kwargs,
            ):
                # Map subagent namespace to tool call id
                # https://github.com/langchain-ai/langgraph/issues/6714
                meta = {
                    'subagent': None,
                }
                if namespace and (src := namespace[0] if isinstance(namespace[0], str) else str(namespace[0])):
                    if src not in namespace_to_tool_call_id and pending_tool_call_ids:
                        namespace_to_tool_call_id[src] = pending_tool_call_ids.pop(0)
                    meta['subagent'] = namespace_to_tool_call_id.get(src)

                # Stream messages and tool calls
                if stream_mode == 'messages' and isinstance(chunk[0], AIMessage):
                    if m := format_message(chunk[0]):
                        yield {
                            'type': 'text',
                            'content': m,
                            **meta,
                        }
                elif stream_mode == 'updates' and isinstance(chunk, dict) and \
                    (messages := (chunk.get('model') or {}).get('messages')) and len(messages) >= 1 and isinstance(messages[0], AIMessage):
                    ai_message = messages[0]
                    stamp_message_timestamp(ai_message)
                    if any(filter(lambda b: b.get('type') in ['text', 'reasoning'], ai_message.content_blocks)):
                        yield {
                            'type': 'text',
                            'content': {
                                'id': ai_message.id,
                                'role': 'assistant',
                                'timestamp': ai_message.additional_kwargs.get('timestamp') or timezone.now().isoformat(),
                            },
                            **meta,
                        }

                    for c in ai_message.tool_calls:
                        if c.get('name') == 'task' and c.get('id') and isinstance(c.get('args'), dict):
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
                elif stream_mode == 'updates' and isinstance(chunk, dict) and (messages := (chunk.get('tools') or {}).get('messages')):
                    for c in messages:
                        if isinstance(c, ToolMessage):
                            stamp_message_timestamp(c)
                            yield {
                                'type': 'tool_call_status',
                                'content': {
                                    'id': c.tool_call_id,
                                    'name': c.name,
                                    'status': c.status,
                                    'content': c.content,
                                    **copy_keys(c.additional_kwargs or {}, ['timestamp', 'output']),
                                },
                                **meta,
                            }
    except Exception as ex:
        logging.exception(ex)
        yield {
            'type': 'error',
            'content': 'Internal server error',
        }
        raise ex


def get_chat_history(agent, thread: ChatThread):
    thread_exists = LangchainCheckpoint.objects \
        .filter(thread=thread) \
        .exists()
    if not thread_exists:
        raise LangchainCheckpoint.DoesNotExist()

    state = agent.get_state(config={'configurable': {'thread_id': str(thread.id)}})
    messages = []
    tool_calls = []
    for m in state.values.get('messages', []):
        if isinstance(m, AIMessage):
            for tc in m.tool_calls:
                tool_calls.append(copy_keys(tc, ['id', 'name', 'args']))

        formatted = format_message(m)
        if not formatted:
            continue

        if isinstance(m, ToolMessage):
            existing_tc = next((tc for tc in tool_calls if tc['id'] == m.tool_call_id), None)
            formatted['tool_call'].update({
                'args': existing_tc['args'] if existing_tc else {},
            })
        messages.append(formatted)

    return {
        'id': thread.id,
        'project': thread.project_id,
        'messages': messages,
    }
