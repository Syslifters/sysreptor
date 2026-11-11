import json
import logging
import os

import django.contrib.postgres.fields
from decouple import strtobool
from django.conf import settings
from django.db import migrations, models

ROLE_FLAGS = [
    ('is_project_admin', 'project_admin'),
    ('is_template_editor', 'template_editor'),
    ('is_designer', 'designer'),
    ('is_user_manager', 'user_manager'),
    ('is_global_archiver', 'global_archiver'),
]

GUEST_BASE_PERMISSIONS = [
    'project.read',
    'project.export',
    'template.read',
    'design.global.read',
    'design.global.export',
]

GUEST_PERMISSION_SETTINGS = [
    ('GUEST_USERS_CAN_CREATE_PROJECTS', True, ['project.create']),
    ('GUEST_USERS_CAN_IMPORT_PROJECTS', False, ['project.import']),
    ('GUEST_USERS_CAN_EDIT_PROJECTS', True, ['project.edit_content']),
    ('GUEST_USERS_CAN_UPDATE_PROJECT_SETTINGS', True, ['project.update_settings']),
    ('GUEST_USERS_CAN_DELETE_PROJECTS', True, ['project.delete']),
    ('GUEST_USERS_CAN_SEE_ALL_USERS', False, ['user.list_all']),
    ('GUEST_USERS_CAN_SHARE_NOTES', False, ['project.share_notes']),
    ('PROJECT_MEMBERS_CAN_ARCHIVE_PROJECTS', True, ['project.archive', 'project.restore']),
]


def _is_set_in_env(name):
    return getattr(settings, 'LOAD_CONFIGURATIONS_FROM_ENV', False) and name in os.environ


def _load_bool_config_value(DbConfigurationEntry, name, default):
    if _is_set_in_env(name):
        value = os.environ.get(name, '')
        return False if not value else bool(strtobool(value))

    if getattr(settings, 'LOAD_CONFIGURATIONS_FROM_DB', False):
        entry = DbConfigurationEntry.objects.filter(name=name).first()
        if entry and entry.value is not None:
            try:
                return bool(json.loads(entry.value))
            except (json.JSONDecodeError, TypeError):
                pass

    return default


def migrate_to_roles(apps, schema_editor):
    PentestUser = apps.get_model('users', 'PentestUser')
    DbConfigurationEntry = apps.get_model('api_utils', 'DbConfigurationEntry')

    # Migrate permission flags to roles
    users_to_update = []
    for user in PentestUser.objects.all():
        roles = []
        if not user.is_system_user:
            roles.append('guest' if user.is_guest else 'regular_user')
            roles.extend(role for flag, role in ROLE_FLAGS if getattr(user, flag))
        user.roles = roles
        users_to_update.append(user)
    PentestUser.objects.bulk_update(users_to_update, fields=['roles'], batch_size=500)

    # Create guest role if it doesn't exist
    if PentestUser.objects.filter(is_guest=True).exists():
        if _is_set_in_env('CUSTOM_USER_ROLES') or DbConfigurationEntry.objects.filter(name='CUSTOM_USER_ROLES').exists():
            logging.warning('CUSTOM_USER_ROLES is already configured. Skipping creation of "guest" role. Make sure to define a "guest" role for guest users.')
        else:
            guest_permissions = list(GUEST_BASE_PERMISSIONS)
            for name, default, permissions in GUEST_PERMISSION_SETTINGS:
                if _load_bool_config_value(DbConfigurationEntry, name, default):
                    guest_permissions.extend(permissions)
            DbConfigurationEntry.objects.create(name='CUSTOM_USER_ROLES', value=json.dumps([
                {'id': 'guest', 'name': 'Guest', 'permissions': guest_permissions},
            ]))

    if not _load_bool_config_value(DbConfigurationEntry, 'PROJECT_MEMBERS_CAN_ARCHIVE_PROJECTS', True):
        logging.warning('PROJECT_MEMBERS_CAN_ARCHIVE_PROJECTS=False is not supported anymore. Users with the "regular_user" role can archive and restore projects. Use custom roles to restrict archive permissions.')

    DbConfigurationEntry.objects \
        .filter(name__in=[name for name, _default, _permissions in GUEST_PERMISSION_SETTINGS]) \
        .delete()


def reverse_migrate_to_roles(apps, schema_editor):
    PentestUser = apps.get_model('users', 'PentestUser')
    DbConfigurationEntry = apps.get_model('api_utils', 'DbConfigurationEntry')

    users_to_update = []
    for user in PentestUser.objects.all():
        roles = set(user.roles or [])
        user.is_guest = not user.is_system_user and 'regular_user' not in roles
        for flag, role in ROLE_FLAGS:
            setattr(user, flag, role in roles)
        users_to_update.append(user)
    PentestUser.objects.bulk_update(users_to_update, fields=['is_guest'] + [flag for flag, _role in ROLE_FLAGS], batch_size=500)

    # Restore GUEST_* settings from guest role
    custom_roles_entry = DbConfigurationEntry.objects.filter(name='CUSTOM_USER_ROLES').first()
    try:
        custom_roles = json.loads(custom_roles_entry.value) if custom_roles_entry else []
    except (json.JSONDecodeError, TypeError):
        custom_roles = []
    guest_role = next((r for r in custom_roles if isinstance(r, dict) and r.get('id') == 'guest'), None)
    if guest_role:
        guest_permissions = set(guest_role.get('permissions') or [])
        DbConfigurationEntry.objects.bulk_create([
            DbConfigurationEntry(name=name, value=json.dumps(all(p in guest_permissions for p in permissions)))
            for name, _default, permissions in GUEST_PERMISSION_SETTINGS
            if not DbConfigurationEntry.objects.filter(name=name).exists()
        ])


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0020_session_user'),
        ('api_utils', '0003_dbconfigurationentry'),
    ]

    operations = [
        migrations.AddField(
            model_name='pentestuser',
            name='roles',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=255), blank=True, db_index=True, default=list, size=None),
        ),
        migrations.RunPython(migrate_to_roles, reverse_migrate_to_roles),
        migrations.RemoveField(
            model_name='pentestuser',
            name='is_designer',
        ),
        migrations.RemoveField(
            model_name='pentestuser',
            name='is_global_archiver',
        ),
        migrations.RemoveField(
            model_name='pentestuser',
            name='is_guest',
        ),
        migrations.RemoveField(
            model_name='pentestuser',
            name='is_project_admin',
        ),
        migrations.RemoveField(
            model_name='pentestuser',
            name='is_template_editor',
        ),
        migrations.RemoveField(
            model_name='pentestuser',
            name='is_user_manager',
        ),
    ]
