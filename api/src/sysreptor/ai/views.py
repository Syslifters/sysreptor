
from asgiref.sync import async_to_sync
from channels.layers import channel_layers
from rest_framework import mixins, renderers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.settings import api_settings

from sysreptor.ai.models import AgentRunStatus, ChatThread
from sysreptor.ai.runs import (
    cancel_run,
    ensure_thread_not_stale,
    to_subscriber_sse,
)
from sysreptor.utils.api import StreamingHttpResponseAsync, ViewSetAsync
from sysreptor.utils.configuration import configuration
from sysreptor.utils.utils import copy_keys


class EventStreamRenderer(renderers.BaseRenderer):
    media_type = 'text/event-stream'
    format = 'event-stream'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data


class ChatThreadPermissions(BasePermission):
    def has_permission(self, request, view):
        if not configuration.AI_AGENT_ENABLED:
            raise PermissionDenied('AI agent chat is disabled in settings')
        if view.action in ['list', 'retrieve']:
            return True
        if 'default' not in channel_layers:
            return False
        from sysreptor.ai.agents.base import get_model_configs
        if not get_model_configs(include_hidden=False):
            raise PermissionDenied('No LLM models configured in settings')
        return True


class ChatThreadViewSet(mixins.ListModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet, ViewSetAsync):
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES + [ChatThreadPermissions]

    def get_queryset(self):
        qs = ChatThread.objects \
            .only_permitted(self.request.user) \
            .filter_visible() \
            .order_by('-created')
        if self.action == 'list':
            project = self.request.GET.get('project')
            if project:
                qs = qs.filter(project_id=project)
        return qs

    def get_serializer_class(self):
        from sysreptor.ai.serializers import ChatThreadListSerializer, ChatThreadSerializer, LLMAgentSerializer
        if self.action == 'create':
            return LLMAgentSerializer
        if self.action == 'list':
            return ChatThreadListSerializer
        return ChatThreadSerializer

    def get_renderers(self):
        if self.action == 'stream':
            return [EventStreamRenderer()]
        return super().get_renderers()

    async def create(self, request, *args, **kwargs):
        serializer = await self.aget_valid_serializer(data=request.data)
        thread_id, run_id = await serializer.start()
        return Response({
            'thread_id': str(thread_id),
            'run_id': str(run_id),
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        from sysreptor.ai.agents import get_agent, get_chat_history

        instance = self.get_object()

        async_to_sync(ensure_thread_not_stale)(instance)
        instance.refresh_from_db()

        data = get_chat_history(agent=get_agent('project_ask'), thread=instance)
        data |= copy_keys(instance, ['title', 'agent', 'model', 'run_id', 'run_status', 'run_error'])
        data.pop('covered', None)

        return Response(data=data)

    def perform_destroy(self, instance):
        if instance.run_status == AgentRunStatus.RUNNING:
            async_to_sync(cancel_run)(instance)
        instance.delete()

    @action(detail=True, methods=['post'])
    async def cancel(self, request, *args, **kwargs):
        thread = await self.aget_object()
        run_id = await cancel_run(thread)
        if not run_id:
            raise NotFound('No active run')
        return Response({'status': 'ok', 'run_id': str(run_id)})

    @action(detail=True, methods=['get'], url_path='stream')
    async def stream(self, request, *args, **kwargs):
        thread = await self.aget_object()
        return StreamingHttpResponseAsync(
            streaming_content=to_subscriber_sse(thread),
            content_type='text/event-stream',
        )

    def handle_exception(self, exc):
        # Event stream renderers do not render exceptions, so re-perform content
        # negotiation with default renderers.
        self.get_renderers = lambda *args, **kwargs: [r() for r in api_settings.DEFAULT_RENDERER_CLASSES]
        neg = self.perform_content_negotiation(self.request, force=True)
        self.request.accepted_renderer, self.request.accepted_media_type = neg
        return super().handle_exception(exc)
