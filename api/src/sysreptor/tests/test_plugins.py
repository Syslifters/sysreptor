import io
import os
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

import pytest
from django.apps import apps
from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.management import call_command
from django.db import ProgrammingError
from django.test import override_settings
from django.urls import reverse

from sysreptor.api_utils.models import DbConfigurationEntry
from sysreptor.conf.plugins import available_plugins, load_plugins, resolve_enabled_plugins
from sysreptor.management.commands import restorebackup
from sysreptor.tests.mock import api_client, create_user, override_configuration
from sysreptor.utils.configuration import configuration
from sysreptor.utils.utils import omit_keys

DEMOPLUGIN_ID = 'db365aa0-ed36-4e90-93b6-a28effc4ed47'
DEMOPLUGIN_APPLABEL = 'plugin_db365aa0ed364e9093b6a28effc4ed47'


@contextmanager
def enable_demoplugin():
    # Import config to check if plugin exists
    try:
        from sysreptor_plugins.demoplugin.apps import DemoPluginConfig  # type: ignore
    except ImportError:
        pytest.skip('DemoPlugin not found')

    app_class = DemoPluginConfig.__module__ + '.' + DemoPluginConfig.__name__
    plugin_enabled_in_config = 'demoplugin' in configuration.ENABLED_PLUGINS or DEMOPLUGIN_ID in configuration.ENABLED_PLUGINS
    plugin_installed = app_class in settings.INSTALLED_APPS
    if plugin_enabled_in_config and plugin_installed and _is_demoplugin_migrated():
        yield
        return

    enabled_plugins = list(configuration.ENABLED_PLUGINS)
    if not plugin_enabled_in_config:
        enabled_plugins = enabled_plugins + ['demoplugin']

    installed_apps = settings.INSTALLED_APPS if plugin_installed else settings.INSTALLED_APPS + [app_class]
    with override_settings(
        INSTALLED_APPS=installed_apps,
    ), override_configuration(
        ENABLED_PLUGINS=enabled_plugins,
    ):
        call_command('migrate', app_label=DEMOPLUGIN_APPLABEL, interactive=False)
        yield


def _is_demoplugin_migrated() -> bool:
    from django.db import connection
    from django.db.migrations.recorder import MigrationRecorder

    return MigrationRecorder(connection).migration_qs.filter(app=DEMOPLUGIN_APPLABEL).exists()


@contextmanager
def disable_demoplugin():
    with override_settings(
        INSTALLED_APPS=[app for app in settings.INSTALLED_APPS if app != 'sysreptor_plugins.demoplugin.apps.DemoPluginConfig'],
    ), override_configuration(
        ENABLED_PLUGINS=[p for p in configuration.ENABLED_PLUGINS if p not in ['demoplugin', DEMOPLUGIN_ID]],
    ):
        yield


def create_demopluginmodel(**kwargs):
    from sysreptor_plugins.demoplugin.models import DemoPluginModel  # type: ignore
    return DemoPluginModel.objects.create(**kwargs)


@pytest.mark.django_db()
class TestPluginLoading:
    @enable_demoplugin()
    def test_plugin_loading(self):
        user = create_user(is_superuser=True, admin_permissions_enabled=True)
        client_admin = api_client(user)

        # Test django app of plugin is installed
        assert apps.is_installed('sysreptor_plugins.demoplugin')
        app_config = apps.get_app_config(DEMOPLUGIN_APPLABEL)
        assert app_config is not None

        # Models registered
        model = apps.get_model(DEMOPLUGIN_APPLABEL, 'DemoPluginModel')
        obj = model.objects.create(name='test')
        assert model.objects.filter(pk=obj.pk).exists()

        # Static files
        # Create dummy file when the frontend was not built yet
        from sysreptor_plugins import demoplugin  # noqa: I001
        pluginjs_path = (Path(demoplugin.__path__[0]) / 'static' / 'plugin.js').resolve()
        if not pluginjs_path.exists():
            pluginjs_path.parent.mkdir(parents=True, exist_ok=True)
            pluginjs_path.touch()
        finders.get_finder.cache_clear()

        res = finders.find(f'plugins/{DEMOPLUGIN_ID}/plugin.js') is not None

        # URLs registered
        assert api_client().get(reverse(f'{DEMOPLUGIN_APPLABEL}:helloworld')).status_code == 200

        # Plugin frontend_config in api settings
        res = api_client().get(reverse('publicutils-settings'))
        assert res.status_code == 200
        demoplugin_config = next(filter(lambda p: p['id'] == DEMOPLUGIN_ID, res.data['plugins']))
        assert omit_keys(demoplugin_config, ['frontend_entry']) == {'id': DEMOPLUGIN_ID, 'name': 'demoplugin', 'frontend_settings': {
            'setting_value': configuration.PLUGIN_DEMOPLUGIN_SETTING,
        }}

        # Plugin settings regsitered
        configuration.clear_cache()
        assert configuration.PLUGIN_DEMOPLUGIN_SETTING == app_config.configuration_definition['PLUGIN_DEMOPLUGIN_SETTING'].default
        res = client_admin.get(reverse('configuration-definition'))
        assert any(d['id'] == 'PLUGIN_DEMOPLUGIN_SETTING' for d in next(filter(lambda p: p['id'] == DEMOPLUGIN_ID, res.data['plugins']))['fields'])
        assert client_admin.get(reverse('configuration-list')).data['PLUGIN_DEMOPLUGIN_SETTING'] == configuration.PLUGIN_DEMOPLUGIN_SETTING


    def test_load_professional_only(self):
        from sysreptor_plugins.demoplugin.apps import DemoPluginConfig  # type: ignore

        try:
            DemoPluginConfig.professional_only = True
            with mock.patch('sysreptor.conf.plugins.can_load_professional_plugins', return_value=False):
                with override_configuration(ENABLED_PLUGINS=['demoplugin']):
                    assert load_plugins({
                        'PLUGIN_DIRS': settings.PLUGIN_DIRS,
                        'DATABASES': settings.DATABASES,
                        'LOAD_CONFIGURATIONS_FROM_ENV': True,
                        'LOAD_CONFIGURATIONS_FROM_DB': False,
                    }) == []
        finally:
            DemoPluginConfig.professional_only = False

    @disable_demoplugin()
    def test_load_settings_of_disabled_plugins(self):
        assert not apps.is_installed(DEMOPLUGIN_APPLABEL)
        config = next(filter(lambda p: p.plugin_id == DEMOPLUGIN_ID, available_plugins))
        assert configuration.PLUGIN_DEMOPLUGIN_SETTING == config.configuration_definition['PLUGIN_DEMOPLUGIN_SETTING'].default


@pytest.mark.django_db(transaction=True)
class TestPluginBackupRestore:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.client = api_client(create_user(is_system_user=True))
        self.backup_key = 'a' * 30
        with override_settings(BACKUP_KEY=self.backup_key):
            yield

    def create_backup(self):
        res = self.client.post(reverse('utils-backup'), data={'key': self.backup_key})
        assert res.status_code == 200
        return b''.join(res.streaming_content)

    def restore_backup(self, backup):
        call_command(restorebackup.Command(), file=io.BytesIO(backup), keepfiles=True)

    @enable_demoplugin()
    def test_backup_restore_plugin_data(self):
        # Create plugin data
        obj = create_demopluginmodel(name='test')
        # Backup data
        self.restore_backup(self.create_backup())
        # Validate data restored
        obj.refresh_from_db()

    def test_backup_restore_plugin_disabled(self):
        with enable_demoplugin():
            obj = create_demopluginmodel(name='test')
            backup = self.create_backup()

        with disable_demoplugin():
            self.restore_backup(backup)

            with pytest.raises(ProgrammingError, match=f'relation "{DEMOPLUGIN_APPLABEL}_demopluginmodel" does not exist'):
                obj.refresh_from_db()

    def test_backup_restore_new_plugin(self):
        with enable_demoplugin():
            obj = create_demopluginmodel()

        with disable_demoplugin():
            backup = self.create_backup()

        with enable_demoplugin():
            self.restore_backup(backup)

            # Not in backup, because plugin was disabled when the backup was created
            with pytest.raises(obj.DoesNotExist):
                obj.refresh_from_db()
            # Can create new models
            create_demopluginmodel()


@pytest.mark.django_db(transaction=True)
class TestEnabledPluginLoading:
    @pytest.mark.parametrize(('enabled_plugins_db', 'enabled_plugins_env', 'expected'), [
        (['database'], ['env'], ['env']),
        (['database'], None, ['database']),
        (None, ['env'], ['env']),
        (None, None, []),
    ])
    @override_configuration(ENABLED_PLUGINS=[])
    def test_load_enabled_plugins(self, enabled_plugins_db, enabled_plugins_env, expected):
        configuration._force_override.pop('ENABLED_PLUGINS', None)
        DbConfigurationEntry.objects.filter(name='ENABLED_PLUGINS').delete()
        if enabled_plugins_db is not None:
            DbConfigurationEntry.objects.create(name='ENABLED_PLUGINS', value=configuration._encode_json_value(enabled_plugins_db))
        with mock.patch.dict(os.environ, {'ENABLED_PLUGINS': ','.join(enabled_plugins_env or [])}):
            if enabled_plugins_env is None:
                del os.environ['ENABLED_PLUGINS']

            assert resolve_enabled_plugins(databases=settings.DATABASES) == expected
