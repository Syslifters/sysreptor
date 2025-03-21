from django.db import models

from sysreptor.users.models import PentestUser
from sysreptor.utils.models import BaseModel


class LanguageToolIgnoreWords(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField(auto_created=True)
    updated_at = models.DateTimeField(auto_now=True)
    user_id = models.BigIntegerField(db_index=True)
    ignore_word = models.CharField(max_length=255)

    class Meta:
        db_table = 'ignore_words'

    def __str__(self):
        return self.ignore_word


class BackupLogType(models.TextChoices):
    SETUP = 'setup', 'Setup'
    BACKUP = 'backup', 'Backup'
    RESTORE = 'restore', 'Restore'


class BackupLog(BaseModel):
    type = models.CharField(choices=BackupLogType.choices, max_length=20)
    user = models.ForeignKey(PentestUser, on_delete=models.SET_NULL, null=True, blank=True)


class DbConfigurationEntry(models.Model):
    name = models.CharField(max_length=255, primary_key=True)
    value = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name
