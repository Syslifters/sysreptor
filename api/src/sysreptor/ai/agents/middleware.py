from collections.abc import Awaitable, Callable

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain_core.messages import merge_message_runs


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
