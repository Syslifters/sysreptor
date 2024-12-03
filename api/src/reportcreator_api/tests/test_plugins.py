import io
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

from reportcreator_api.conf.plugins import load_plugins
from reportcreator_api.management.commands import restorebackup
from reportcreator_api.tests.mock import api_client, create_user
from reportcreator_api.utils.license import LicenseType
from reportcreator_api.utils.utils import omit_keys

DEMOPLUGIN_ID = 'db365aa0-ed36-4e90-93b6-a28effc4ed47'
DEMOPLUGIN_APPLABEL = 'plugin_db365aa0ed364e9093b6a28effc4ed47'


@contextmanager
def enable_demoplugin():
    # Import config to check if plugin exists
    try:
        from sysreptor_plugins.demoplugin.app import DemoPluginConfig
    except ImportError:
        pytest.skip('DemoPlugin not found')

    if 'demoplugin' in settings.ENABLED_PLUGINS or DEMOPLUGIN_ID in settings.ENABLED_PLUGINS:
        yield
        return

    with override_settings(
        ENABLED_PLUGINS=settings.ENABLED_PLUGINS + ['demoplugin'],
        INSTALLED_APPS=settings.INSTALLED_APPS + [DemoPluginConfig.__module__ + '.' + DemoPluginConfig.__name__],
    ):
        call_command('migrate', app_label=DEMOPLUGIN_APPLABEL, interactive=False)
        yield


@contextmanager
def disable_demoplugin():
    with override_settings(
        ENABLED_PLUGINS=[plugin for plugin in settings.ENABLED_PLUGINS if plugin not in ['demoplugin', DEMOPLUGIN_ID]],
        INSTALLED_APPS=[app for app in settings.INSTALLED_APPS if app != 'sysreptor_plugins.demoplugin.app.DemoPluginConfig'],
    ):
        yield


def create_demopluginmodel(**kwargs):
    from sysreptor_plugins.demoplugin.models import DemoPluginModel
    return DemoPluginModel.objects.create(**kwargs)


@pytest.mark.django_db()
class TestPluginLoading:
    @enable_demoplugin()
    def test_plugin_loading(self):
        # Test django app of plugin is installed
        assert apps.is_installed('sysreptor_plugins.demoplugin')
        assert apps.get_app_config(DEMOPLUGIN_APPLABEL) is not None

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

        # Plugin config in api settings
        res = api_client().get(reverse('publicutils-settings'))
        assert res.status_code == 200
        demoplugin_config = next(filter(lambda p: p['id'] == DEMOPLUGIN_ID, res.data['plugins']))
        assert omit_keys(demoplugin_config, ['frontend_entry']) == {'id': DEMOPLUGIN_ID, 'name': 'demoplugin', 'frontend_settings': {}}

    @mock.patch('reportcreator_api.utils.license.decode_and_validate_license', return_value={'type': LicenseType.COMMUNITY, 'users': 3, 'error': None})
    def test_load_professional_only(self, _mock):
        from sysreptor_plugins.demoplugin.app import DemoPluginConfig

        try:
            DemoPluginConfig.professional_only = True
            assert load_plugins(plugin_dirs=settings.PLUGIN_DIRS, enabled_plugins=['demoplugin']) == []
        finally:
            DemoPluginConfig.professional_only = False

@pytest.mark.django_db()
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
                assert not obj.__class__.objects.filter(pk=obj.pk).exists()

    def test_backup_restore_new_plugin(self):
        with enable_demoplugin():
            obj = create_demopluginmodel()

        with disable_demoplugin():
            backup = self.create_backup()

        with enable_demoplugin():
            self.restore_backup(backup)

            # Not in backup, because plugin was disabled
            with pytest.raises(obj.DoesNotExist):
                obj.refresh_from_db()
            # Can create new models
            create_demopluginmodel()

