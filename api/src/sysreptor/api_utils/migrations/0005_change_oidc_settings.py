import json
import os

from django.db import migrations

from sysreptor.utils.configuration import configuration
from sysreptor.utils.utils import is_json_string


def migrate_oidc_settings(apps, schema_editor):
    DbConfigurationEntry = apps.get_model('api_utils', 'DbConfigurationEntry')

    db_config_entries = dict(DbConfigurationEntry.objects.all().values_list('name', 'value'))
    def get_config(name):
        if name in os.environ:
            return os.environ[name]
        else:
            return configuration._decode_json_value(db_config_entries.get(name))

    config_changed = False
    oidc_authlib_oauth_clients = get_config('OIDC_AUTHLIB_OAUTH_CLIENTS')
    if isinstance(oidc_authlib_oauth_clients, dict):
        pass
    elif is_json_string(oidc_authlib_oauth_clients):
        oidc_authlib_oauth_clients = json.loads(oidc_authlib_oauth_clients)
    else:
        oidc_authlib_oauth_clients = {}
    if not isinstance(oidc_authlib_oauth_clients, dict):
        oidc_authlib_oauth_clients = {}

    if (
        (azure_client_id := get_config('OIDC_AZURE_CLIENT_ID')) and
        (azure_client_secret := get_config('OIDC_AZURE_CLIENT_SECRET')) and
        (azure_tenant_id := get_config('OIDC_AZURE_TENANT_ID')) and
        'azure' not in oidc_authlib_oauth_clients
    ):
        oidc_authlib_oauth_clients['azure'] = {
            'label': 'Microsoft Entra ID',
            'client_id': azure_client_id,
            'client_secret': azure_client_secret,
            'server_metadata_url': f'https://login.microsoftonline.com/{azure_tenant_id}/v2.0/.well-known/openid-configuration',
            'client_kwargs': {
                'scope': 'openid email profile',
                'code_challenge_method': 'S256',
            },
            'reauth_supported': True,
            'require_email_verified': False,
        }
        config_changed = True

    if (
        (google_client_id := get_config('OIDC_GOOGLE_CLIENT_ID')) and
        (google_client_secret := get_config('OIDC_GOOGLE_CLIENT_SECRET')) and
        'google' not in oidc_authlib_oauth_clients
    ):
        oidc_authlib_oauth_clients['google'] = {
            'label': 'Google',
            'client_id': google_client_id,
            'client_secret': google_client_secret,
            'server_metadata_url': 'https://accounts.google.com/.well-known/openid-configuration',
            'client_kwargs': {
                'scope': 'openid email profile',
                'code_challenge_method': 'S256',
            },
            'reauth_supported': False,
            'require_email_verified': False,
        }
        config_changed = True

    if config_changed:
        value = configuration._encode_json_value(value=json.dumps(oidc_authlib_oauth_clients, indent=2))
        DbConfigurationEntry.objects.filter(name__in=[
            'OIDC_AZURE_CLIENT_ID', 'OIDC_AZURE_CLIENT_SECRET', 'OIDC_AZURE_TENANT_ID',
            'OIDC_GOOGLE_CLIENT_ID', 'OIDC_GOOGLE_CLIENT_SECRET',
        ]).delete()
        DbConfigurationEntry.objects.update_or_create(
            name='OIDC_AUTHLIB_OAUTH_CLIENTS',
            defaults={'value': value},
            create_defaults={'value': value},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('api_utils', '0004_alter_backuplog_type'),
    ]

    operations = [
        migrations.RunPython(code=migrate_oidc_settings, reverse_code=migrations.RunPython.noop),
    ]
