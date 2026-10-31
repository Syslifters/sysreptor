from django.db.models import Prefetch
from drf_spectacular.utils import OpenApiTypes, extend_schema_field
from rest_framework import serializers

from sysreptor.ai.models import AgentMode, ChatThread
from sysreptor.pentests.models import PentestProject, ProjectNotebookPage
from sysreptor.utils.serializers import OptionalPrimaryKeyRelatedField


def truncate_title(text: str, max_length: int = 80) -> str:
    collapsed = ' '.join((text or '').split())
    if len(collapsed) <= max_length:
        return collapsed
    return collapsed[: max_length - 1].rstrip() + '…'


@extend_schema_field(OpenApiTypes.STR)
class ProjectRelatedField(OptionalPrimaryKeyRelatedField):
    def get_queryset(self):
        return PentestProject.objects \
            .only_permitted(self.context['request'].user) \
            .select_related('project_type') \
            .prefetch_related('findings', 'sections', Prefetch('notes', ProjectNotebookPage.objects.select_related('parent')))


class ChatThreadSerializer(serializers.ModelSerializer):
    messages = serializers.ListField(child=serializers.DictField())
    interrupts = serializers.ListField(child=serializers.DictField(), allow_empty=True)

    class Meta:
        model = ChatThread
        fields = [
            'id', 'project', 'title', 'agent', 'model',
            'messages', 'interrupts', 'run_id', 'run_status', 'run_error',
        ]


class ChatThreadListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatThread
        fields = ['id', 'project', 'title', 'agent', 'model', 'run_status', 'created', 'updated']


class LLMAgentSerializer(serializers.Serializer):
    agent = serializers.ChoiceField(choices=AgentMode.choices, required=False, allow_null=True)
    model = serializers.CharField(required=False, allow_null=True)
    id = serializers.UUIDField(required=False, allow_null=True)
    messages = serializers.ListField(child=serializers.CharField(), required=False, allow_null=True)
    resume = serializers.JSONField(required=False, allow_null=True)
    context = serializers.DictField(child=serializers.CharField(), required=False, allow_null=True)
    project = ProjectRelatedField()

    def validate(self, attrs):
        from sysreptor.ai.agents.base import get_model_configs

        thread_id = attrs.get('id')
        messages = attrs.get('messages') or []
        resume = attrs.get('resume')
        if resume is not None:
            if not thread_id:
                raise serializers.ValidationError('id is required when resuming')
        elif not thread_id and not messages:
            raise serializers.ValidationError('messages are required')
        elif thread_id and not messages and resume is None:
            raise serializers.ValidationError('id requires messages')

        thread = ChatThread.objects \
            .only_permitted(self.context['request'].user) \
            .filter(id=thread_id) \
            .select_related('user', 'project') \
            .first() if thread_id else None
        if thread_id and not thread:
            raise serializers.ValidationError('Invalid id')

        attrs['agent'] = attrs.get('agent') or (thread.agent if thread else None)
        if not attrs['agent']:
            raise serializers.ValidationError({'agent': 'This field is required.'})
        if not attrs.get('model') and thread:
            attrs['model'] = thread.model
        if attrs.get('model') and not any(m['id'] == attrs['model'] for m in get_model_configs(include_hidden=False)):
            raise serializers.ValidationError('Invalid model')

        attrs['agent_instance'], thread_filters = self.get_agent(attrs)
        if thread:
            if any(getattr(thread, key) != value for key, value in thread_filters.items()):
                raise serializers.ValidationError('Invalid id')
            if (thread.agent, thread.model) != (attrs['agent'], attrs.get('model')):
                thread.agent = attrs['agent']
                thread.model = attrs.get('model')
                thread.save(update_fields=['agent', 'model'])
            attrs['thread'] = thread
        else:
            attrs['thread'] = ChatThread.objects.create(
                user=self.context['request'].user,
                title=truncate_title(messages[0]) if messages else '',
                agent=attrs['agent'],
                model=attrs.get('model'),
                **thread_filters,
            )
        return super().validate(attrs)

    def get_agent(self, attrs):
        from sysreptor.ai.agents import get_agent

        if attrs.get('agent') not in AgentMode.values:
            raise serializers.ValidationError('Invalid agent type')
        if not attrs.get('project'):
            raise serializers.ValidationError('Project is required for project agent')
        return get_agent(attrs['agent']), {'project': attrs['project']}

    async def start(self):
        from sysreptor.ai.models import AgentRunStatus
        from sysreptor.ai.runs import end_run, start_run
        from sysreptor.ai.tasks import run_agent

        thread = self.validated_data['thread']
        messages = self.validated_data.get('messages') or []
        message = messages[0] if messages else None

        run_id = await start_run(thread=thread)
        try:
            await run_agent(
                thread_id=str(thread.id),
                run_id=str(run_id),
                agent=self.validated_data['agent'],
                model=self.validated_data.get('model'),
                message=message,
                resume=self.validated_data.get('resume'),
                context=self.validated_data.get('context') or {},
                admin_permissions_enabled=self.context['request'].user.is_admin,
            )
        except Exception:
            await end_run(thread=thread, status=AgentRunStatus.ERROR, error='Failed to enqueue agent run')
            raise
        return thread.id, run_id
