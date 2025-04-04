from django.db import models
from sysreptor.utils.models import BaseModel


class ProjectNumber(BaseModel):
    """
    Model to store the continuous counting number for PentestProject.
    """
    current_id = models.PositiveIntegerField(default=0)
