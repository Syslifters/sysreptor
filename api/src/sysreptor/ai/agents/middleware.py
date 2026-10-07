from collections.abc import Awaitable, Callable

from django.utils import timezone
from langchain.agents.middleware import AgentMiddleware, AgentState, ModelRequest, ModelResponse
from langchain.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.messages import merge_message_runs


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
