from django.db import models
from reportcreator_api.utils.models import BaseModel


class TestPluginModel(BaseModel):
    """
    Database table added by plugin.
    Migrations are managed by django.

    Create migrations with: cd dev; docker compose run dev api python3 manage.py makemigrations plugin_<plugin_id>

    """
    name = models.CharField(max_length=255)
