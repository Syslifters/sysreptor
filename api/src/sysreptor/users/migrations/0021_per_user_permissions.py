import json
import os

from decouple import strtobool
from django.conf import settings
from django.db import migrations, models

PERMISSION_FIELDS = [
    ('can_create_projects', 'GUEST_USERS_CAN_CREATE_PROJECTS', 'DEFAULT_PERMISSION_CAN_CREATE_PROJECTS', True),
    ('can_import_projects', 'GUEST_USERS_CAN_IMPORT_PROJECTS', 'DEFAULT_PERMISSION_CAN_IMPORT_PROJECTS', False),
    ('can_edit_projects', 'GUEST_USERS_CAN_EDIT_PROJECTS', 'DEFAULT_PERMISSION_CAN_EDIT_PROJECTS', True),
    ('can_update_project_settings', 'GUEST_USERS_CAN_UPDATE_PROJECT_SETTINGS', 'DEFAULT_PERMISSION_CAN_UPDATE_PROJECT_SETTINGS', True),
    ('can_delete_projects', 'GUEST_USERS_CAN_DELETE_PROJECTS', 'DEFAULT_PERMISSION_CAN_DELETE_PROJECTS', True),
    ('can_see_all_users', 'GUEST_USERS_CAN_SEE_ALL_USERS', 'DEFAULT_PERMISSION_CAN_SEE_ALL_USERS', False),
    ('can_share_notes', 'GUEST_USERS_CAN_SHARE_NOTES', 'DEFAULT_PERMISSION_CAN_SHARE_NOTES', False),
]


def _load_guest_config_value(DbConfigurationEntry, guest_name, default):
    if getattr(settings, 'LOAD_CONFIGURATIONS_FROM_ENV', False) and guest_name in os.environ:
        value = os.environ.get(guest_name, '')
        return False if not value else bool(strtobool(value))

    if getattr(settings, 'LOAD_CONFIGURATIONS_FROM_DB', False):
        entry = DbConfigurationEntry.objects.filter(name=guest_name).first()
        if entry and entry.value is not None:
            try:
                return bool(json.loads(entry.value))
            except (json.JSONDecodeError, TypeError):
                pass

    return default


def migrate_guest_permissions(apps, schema_editor):
    PentestUser = apps.get_model('users', 'PentestUser')
    DbConfigurationEntry = apps.get_model('api_utils', 'DbConfigurationEntry')

    values = {
        field: _load_guest_config_value(DbConfigurationEntry, guest_name, default)
        for field, guest_name, _new_name, default in PERMISSION_FIELDS
    }
    PentestUser.objects.filter(is_guest=True).update(**values)

    for _field, guest_name, new_name, _default in PERMISSION_FIELDS:
        if DbConfigurationEntry.objects.filter(name=new_name).exists():
            DbConfigurationEntry.objects.filter(name=guest_name).delete()
            continue
        DbConfigurationEntry.objects.filter(name=guest_name).update(name=new_name)


def reverse_guest_permissions(apps, schema_editor):
    PentestUser = apps.get_model('users', 'PentestUser')
    DbConfigurationEntry = apps.get_model('api_utils', 'DbConfigurationEntry')

    restricted = models.Q()
    for field, _guest_name, _new_name, _default in PERMISSION_FIELDS:
        restricted |= models.Q(**{field: False})
    PentestUser.objects.filter(restricted).update(is_guest=True)
    PentestUser.objects.exclude(restricted).update(is_guest=False)

    for _field, guest_name, new_name, _default in PERMISSION_FIELDS:
        if DbConfigurationEntry.objects.filter(name=guest_name).exists():
            DbConfigurationEntry.objects.filter(name=new_name).delete()
            continue
        DbConfigurationEntry.objects.filter(name=new_name).update(name=guest_name)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0020_session_user'),
        ('api_utils', '0003_dbconfigurationentry'),
    ]

    operations = [
        migrations.AddField(
            model_name='pentestuser',
            name='can_create_projects',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='pentestuser',
            name='can_import_projects',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='pentestuser',
            name='can_edit_projects',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='pentestuser',
            name='can_update_project_settings',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='pentestuser',
            name='can_delete_projects',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='pentestuser',
            name='can_see_all_users',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='pentestuser',
            name='can_share_notes',
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(migrate_guest_permissions, reverse_guest_permissions),
        migrations.RemoveField(
            model_name='pentestuser',
            name='is_guest',
        ),
    ]
