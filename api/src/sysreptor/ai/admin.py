from django.contrib import admin

from sysreptor.ai.models import (
    ChatThread,
    LangchainCheckpoint,
    LangchainCheckpointBlob,
    LangchainCheckpointWrite,
)
from sysreptor.utils.admin import BaseAdmin, admin_changelist_url


@admin.register(ChatThread)
class ChatThreadAdmin(BaseAdmin):
    list_display = ['id', 'user', 'project', 'created']
    list_filter = ['created', 'updated']
    search_fields = ['user__username', 'project__name']
    readonly_fields = ['user', 'project']

    def get_queryset(self, request):
        return super().get_queryset(request) \
            .select_related('user', 'project')

    def link_checkpoints(self, obj):
        return admin_changelist_url('LangchainCheckpoints', 'ai', 'langchaincheckpoint', {'thread__id': obj.id})


@admin.register(LangchainCheckpoint)
class LangchainCheckpointAdmin(BaseAdmin):
    list_display = ['id', 'thread', 'checkpoint_ns', 'checkpoint_id', 'created']
    list_filter = ['created', 'updated']
    readonly_fields = ['checkpoint_id', 'parent_checkpoint_id']


@admin.register(LangchainCheckpointBlob)
class LangchainCheckpointBlobAdmin(BaseAdmin):
    list_display = ['id', 'thread', 'checkpoint_ns', 'channel', 'version', 'type', 'created']
    list_filter = ['type', 'created']
    readonly_fields = ['channel', 'version', 'type']


@admin.register(LangchainCheckpointWrite)
class LangchainCheckpointWriteAdmin(BaseAdmin):
    list_display = ['id', 'thread', 'checkpoint_ns', 'checkpoint_id', 'task_id', 'channel', 'idx', 'created']
    list_filter = ['channel', 'created']
    readonly_fields = ['checkpoint_id', 'task_id', 'task_path', 'idx', 'channel', 'type']
