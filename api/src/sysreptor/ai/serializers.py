from django.db.models import Prefetch
from rest_framework import serializers

from sysreptor.ai.agents import agent_stream, get_agent
from sysreptor.ai.models import ChatThread
from sysreptor.pentests.models import PentestProject, ProjectNotebookPage
from sysreptor.utils.serializers import OptionalPrimaryKeyRelatedField


class ProjectRelatedField(OptionalPrimaryKeyRelatedField):
    def get_queryset(self):
        return PentestProject.objects \
            .only_permitted(self.context['request'].user) \
            .select_related('project_type') \
            .prefetch_related('findings', 'sections', Prefetch('notes', ProjectNotebookPage.objects.select_related('parent')))


class ChatThreadSerializer(serializers.ModelSerializer):
    messages = serializers.ListField(child=serializers.DictField())
    interrupts = serializers.DictField(allow_null=True)

    class Meta:
        model = ChatThread
        fields = ['id', 'project', 'messages', 'interrupts']


class LLMAgentSerializer(serializers.Serializer):
    agent = serializers.ChoiceField(choices=['project_ask', 'project_agent'])
    id = serializers.UUIDField(required=False, allow_null=True)
    messages = serializers.ListField(child=serializers.CharField(), required=False, allow_null=True)
    context = serializers.DictField(child=serializers.CharField(), required=False, allow_null=True)
    project = ProjectRelatedField()

    def validate(self, attrs):
        # Validate message
        thread_id = attrs.get('id')
        messages = attrs.get('messages', [])
        if not thread_id and not messages:
            raise serializers.ValidationError('messages are required')
        if thread_id and not messages:
            raise serializers.ValidationError('id requires messages')

        # Set agent parameters
        attrs['input'] = {'messages': messages}

        # Validate required parameters for agent type
        attrs['agent'], thread_filters = self.get_agent(attrs)

        # Validate thread_id exists and belongs to user
        if thread_id:
            attrs['thread'] = ChatThread.objects \
                .filter(id=thread_id) \
                .filter(user_id=self.context['request'].user.id) \
                .filter(**thread_filters) \
                .first()
            if not attrs['thread']:
                raise serializers.ValidationError('Invalid id')
        else:
            attrs['thread'] = ChatThread.objects.create(
                user_id=self.context['request'].user.id,
                **thread_filters,
            )
        return super().validate(attrs)

    def get_agent(self, attrs):
        if attrs.get('agent') in ['project_ask', 'project_agent']:
            if not attrs.get('project'):
                raise serializers.ValidationError('Project is required for project agent')
            return get_agent(attrs['agent']), {'project': attrs['project']}
        else:
            raise serializers.ValidationError('Invalid agent type')

    def stream(self):
        thread = self.validated_data.get('thread')
        if not thread.id:
            # Create new thread
            thread.save()

        return agent_stream(
            agent=self.validated_data['agent'],
            input=self.validated_data['input'],
            context=self.validated_data.get('context', {}),
            thread=thread,
        )

