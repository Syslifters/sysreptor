from django.db import models
from sysreptor.utils.models import BaseModel


class DemoPluginModel(BaseModel):
    """
    Database table added by plugin.
    Migrations are managed by django.

    Create migrations:
    * mkdir plugins/<dir>/migrations; touch plugins/<dir>/migrations/__init__.py
    * cd dev; docker compose run dev api python3 manage.py makemigrations

    """
    name = models.CharField(max_length=255)
