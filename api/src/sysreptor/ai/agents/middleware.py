from collections.abc import Awaitable, Callable, Sequence

from deepagents.backends.protocol import BackendProtocol
from deepagents.middleware.subagents import (
    _FORK_RECURSION_REFUSAL,
    _FORKED_CONTEXT_KEY,
    CompiledSubAgent,
    SubAgent,
    SubAgentMiddleware,
    _subagent_tracing_context,
)
from django.utils import timezone
from langchain.agents.middleware import AgentMiddleware, AgentState, ModelRequest, ModelResponse
from langchain.messages import AIMessage, HumanMessage, ToolMessage
from langchain.tools import ToolRuntime, tool
from langchain_core.messages import merge_message_runs
from langchain_core.runnables.config import merge_configs
from langchain_core.tools import BaseTool


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


class SelectConfiguredModelMiddleware(AgentMiddleware):
    """
    Select the LLM at runtime from request.runtime.context.model.
    See https://docs.langchain.com/oss/python/deepagents/models#select-a-model-at-runtime
    """

    _model_cache = {}

    def _model_for_request(self, request: ModelRequest):
        from sysreptor.ai.agents.base import get_default_model_id, init_chat_model

        model = getattr(request.runtime.context, 'model', None) or get_default_model_id()
        if model not in self._model_cache:
            self._model_cache[model] = init_chat_model(model)
        return self._model_cache[model]

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        return handler(request.override(model=self._model_for_request(request)))

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        return await handler(request.override(model=self._model_for_request(request)))


class MergeConsecutiveMessagesMiddleware(AgentMiddleware):
    """
    Merge consecutive messages of the same type before model invocation.

    Required for LLM providers that enforce alternating user/assistant roles.
    """

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        return handler(request.override(messages=merge_message_runs(request.messages)))

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        return await handler(request.override(messages=merge_message_runs(request.messages)))


def subagent_checkpoint_ns(subagent_type: str, tool_call_id: str) -> str:
    return f'subagent:{subagent_type}:{tool_call_id}'


class CustomSubagentMiddleware(SubAgentMiddleware):
    def __init__(
        self,
        *,
        backend: BackendProtocol,
        subagents: Sequence[SubAgent | CompiledSubAgent],
        system_prompt: str | None = None,
        task_description: str | None = None,
        private_state_keys: frozenset[str] | None = None,
        state_schema: type | None = None,
    ) -> None:
        super().__init__(
            backend=backend,
            subagents=subagents,
            system_prompt=system_prompt,
            task_description=task_description,
            private_state_keys=private_state_keys,
            state_schema=state_schema,
        )
        self.tools = [self._replace_task_tool(self.tools[0])]

    def _replace_task_tool(self, original: BaseTool) -> BaseTool:
        coro = original.coroutine
        if not coro or not coro.__closure__ or not coro.__code__.co_freevars:
            raise RuntimeError('task tool coroutine is not a closure')

        free = dict(zip(coro.__code__.co_freevars, (c.cell_contents for c in coro.__closure__), strict=True))
        validate_and_prepare = free['_validate_and_prepare_state']
        return_command = free['_return_command_with_state_update']
        graphs = free['subagent_graphs']

        @tool(
            description=original.description,
            args_schema=original.args_schema,
            infer_schema=False,
        )
        async def task(description: str, subagent_type: str, runtime: ToolRuntime):
            if runtime.state.get(_FORKED_CONTEXT_KEY):
                return _FORK_RECURSION_REFUSAL
            if subagent_type not in graphs:
                allowed = ', '.join(f'`{k}`' for k in graphs)
                return f'We cannot invoke subagent {subagent_type} because it does not exist, the only allowed types are {allowed}'
            if not runtime.tool_call_id:
                raise ValueError('Tool call ID is required for subagent invocation')

            subagent, subagent_state = validate_and_prepare(subagent_type, description, runtime)
            config = merge_configs(runtime.config, {'configurable': {'ls_agent_type': 'subagent'}})
            config['configurable'] = dict(config.get('configurable') or {}) | {
                'checkpoint_ns': subagent_checkpoint_ns(subagent_type, runtime.tool_call_id),
            }
            config['configurable'].pop('checkpoint_id', None)
            with _subagent_tracing_context():
                result = await subagent.ainvoke(subagent_state, config)
            return return_command(result, runtime.tool_call_id)

        return task
