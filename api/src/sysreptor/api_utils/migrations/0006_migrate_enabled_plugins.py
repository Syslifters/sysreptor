import os

from django.db import migrations

from sysreptor.conf.plugins import ENABLED_PLUGINS_FIELD
from sysreptor.utils.configuration import configuration


def migrate_enabled_plugins(apps, schema_editor):
    if 'ENABLED_PLUGINS' not in os.environ:
        return

    DbConfigurationEntry = apps.get_model('api_utils', 'DbConfigurationEntry')
    if DbConfigurationEntry.objects.filter(name='ENABLED_PLUGINS').exists():
        return

    enabled = configuration._load_env_value(ENABLED_PLUGINS_FIELD, os.environ['ENABLED_PLUGINS'])
    value = configuration._encode_json_value(value=enabled)
    DbConfigurationEntry.objects.update_or_create(
        name='ENABLED_PLUGINS',
        defaults={'value': value},
        create_defaults={'value': value},
    )


class Migration(migrations.Migration):
    dependencies = [
        ('api_utils', '0005_change_oidc_settings'),
    ]

    operations = [
        migrations.RunPython(code=migrate_enabled_plugins, reverse_code=migrations.RunPython.noop),
    ]
