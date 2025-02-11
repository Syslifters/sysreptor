from django.contrib import admin

from reportcreator_api.api_utils.models import BackupLog, DbConfigurationEntry, LanguageToolIgnoreWords
from reportcreator_api.utils.admin import BaseAdmin


@admin.register(LanguageToolIgnoreWords)
class LanguageToolIgnoreWordsAdmin(admin.ModelAdmin):
    pass


@admin.register(BackupLog)
class BackupLogAdmin(BaseAdmin):
    pass


@admin.register(DbConfigurationEntry)
class DbConfigurationEntryAdmin(admin.ModelAdmin):
    list_display = ['name']

