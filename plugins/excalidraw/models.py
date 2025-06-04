from django.db import models
from sysreptor.pentests.models import PentestProject
from sysreptor.utils.crypto import EncryptedField
from sysreptor.utils.models import BaseModel


class ProjectExcalidrawData(BaseModel):
    project = models.OneToOneField(PentestProject, on_delete=models.CASCADE, unique=True)
    elements = EncryptedField(base_field=models.JSONField(default=list))

