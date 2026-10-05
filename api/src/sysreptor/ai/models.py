from uuid import uuid4

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from sysreptor.ai import querysets
from sysreptor.pentests.models import PentestProject
from sysreptor.users.models import PentestUser
from sysreptor.utils.crypto.fields import EncryptedField
from sysreptor.utils.models import BaseModel


class ChatThread(BaseModel):
    user = models.ForeignKey(PentestUser, on_delete=models.CASCADE)
    project = models.ForeignKey(PentestProject, on_delete=models.CASCADE, null=True, blank=True)

    objects = querysets.ChatThreadManager()


class LangchainCheckpoint(BaseModel):
    thread = models.ForeignKey(ChatThread, on_delete=models.CASCADE, related_name='checkpoints')

    checkpoint_ns = models.CharField(max_length=255, default='', db_index=True)
    checkpoint_id = models.UUIDField(default=uuid4)
    parent_checkpoint_id = models.UUIDField(null=True, blank=True)
    metadata = EncryptedField(base_field=models.BinaryField(), default=b'{}', blank=True)
    checkpoint = EncryptedField(base_field=models.JSONField(default=dict, encoder=DjangoJSONEncoder), default=dict)

    class Meta(BaseModel.Meta):
        unique_together = [('thread', 'checkpoint_ns', 'checkpoint_id')]


class LangchainCheckpointBlob(BaseModel):
    thread = models.ForeignKey(ChatThread, on_delete=models.CASCADE, related_name='checkpoint_blobs')

    checkpoint_ns = models.CharField(max_length=255, default='', db_index=True)
    channel = models.CharField(max_length=255)
    version = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    blob = EncryptedField(base_field=models.BinaryField(), null=True, blank=True)

    class Meta(BaseModel.Meta):
        unique_together = [('thread', 'checkpoint_ns', 'channel', 'version')]


class LangchainCheckpointWrite(BaseModel):
    thread = models.ForeignKey(ChatThread, on_delete=models.CASCADE, related_name='checkpoint_writes')

    checkpoint_ns = models.CharField(max_length=255, default='', db_index=True)
    checkpoint_id = models.UUIDField()
    task_id = models.CharField(max_length=255)
    task_path = models.CharField(max_length=1024, default='', blank=True)
    idx = models.IntegerField()
    channel = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    blob = EncryptedField(base_field=models.BinaryField())

    class Meta(BaseModel.Meta):
        unique_together = [('thread', 'checkpoint_ns', 'checkpoint_id', 'task_id', 'idx')]
        indexes = [
            models.Index(fields=['thread', 'checkpoint_ns', 'checkpoint_id']),
        ]
