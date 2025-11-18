import json

from django.conf import settings
from rest_framework import renderers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.settings import api_settings

from sysreptor.ai.agents import get_agent, get_chat_history
from sysreptor.ai.models import ChatThread
from sysreptor.ai.serializers import ChatThreadSerializer, LLMAgentSerializer
from sysreptor.users.auth import forbidden_with_apitoken_auth
from sysreptor.utils.api import StreamingHttpResponseAsync, ViewSetAsync
from sysreptor.utils.configuration import configuration


async def to_server_sent_events(generator):
    async for event in generator:
        yield f'event: {event['type']}\ndata: {json.dumps(event)}\n\n'.encode()


class EventStreamRenderer(renderers.BaseRenderer):
    media_type = 'text/event-stream'
    format = 'event-stream'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data


class ChatThreadPermissions(BasePermission):
    def has_permission(self, request, view):
        if not configuration.AI_AGENT_ENABLED:
            raise PermissionDenied('AI agent feature is disabled')
        if not settings.AI_AGENT_MODEL:
            raise PermissionDenied('No LLM model configured')

        if view.action == 'create':
            forbidden_with_apitoken_auth(request)
        return True


class ChatThreadViewSet(viewsets.GenericViewSet, ViewSetAsync):
    serializer_class = ChatThreadSerializer
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES + [ChatThreadPermissions]

    def get_queryset(self):
        return ChatThread.objects \
            .filter(user=self.request.user) \
            .filter_has_checkpoints()

    def get_serializer_class(self):
        if self.action == 'create':
            return LLMAgentSerializer
        return super().get_serializer_class()

    def get_renderers(self):
        if self.action == 'create':
            return [EventStreamRenderer()]
        return super().get_renderers()

    async def create(self, request, *args, **kwargs):
        serializer = await self.aget_valid_serializer(data=request.data)
        return StreamingHttpResponseAsync(
            streaming_content=to_server_sent_events(serializer.stream()),
            content_type='text/event-stream',
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        history = get_chat_history(agent=get_agent('project_ask'), thread=instance)
        return Response(data=history)

    @action(detail=False, methods=['get'])
    def latest(self, request, *args, **kwargs):
        if not request.GET.get('project'):
            raise ValidationError('project is required')

        # Get latest thread for project
        thread = self.get_queryset() \
            .filter(project_id=request.GET['project']) \
            .order_by('-created') \
            .first()
        if not thread:
            raise NotFound()

        history = get_chat_history(agent=get_agent('project_ask'), thread=thread)
        return Response(data=history)

    def handle_exception(self, exc):
        # Event stream renderers do not render exceptions, so re-perform content
        # negotiation with default renderers.
        self.get_renderers = lambda *args, **kwargs: [r() for r in api_settings.DEFAULT_RENDERER_CLASSES]
        neg = self.perform_content_negotiation(self.request, force=True)
        self.request.accepted_renderer, self.request.accepted_media_type = neg
        return super().handle_exception(exc)
