from uuid import uuid4

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
    metadata = EncryptedField(base_field=models.BinaryField(), default=dict, blank=True)
    checkpoint_type = models.CharField(max_length=255)
    checkpoint = EncryptedField(base_field=models.BinaryField())
    pending_writes_type = models.CharField(max_length=255, null=True, blank=True)
    pending_writes = EncryptedField(base_field=models.BinaryField(), null=True, blank=True)

    class Meta(BaseModel.Meta):
        unique_together = [('thread', 'checkpoint_ns', 'checkpoint_id')]
