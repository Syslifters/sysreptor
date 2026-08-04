import importlib.util
import logging
import os
import re
import sys
import warnings
from copy import deepcopy
from functools import cached_property
from importlib import import_module
from importlib.machinery import ModuleSpec
from pathlib import Path
from unittest import mock

from decouple import Csv, config
from django.apps import AppConfig, apps
from django.conf import settings
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.finders import AppDirectoriesFinder, FileSystemFinder
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage, storages
from django.db.backends.utils import CursorWrapper
from django.db.utils import ConnectionHandler
from django.utils.functional import classproperty
from django.utils.module_loading import module_has_submodule

from sysreptor.utils import license
from sysreptor.utils.configuration import Configuration
from sysreptor.utils.fielddefinition.types import FieldDefinition, ListField, StringField

available_plugins = []
enabled_plugins = []

SYSREPTOR_PLUGINS_PACKAGE = 'sysreptor_plugins'

ENABLED_PLUGINS_FIELD = ListField(
    id='ENABLED_PLUGINS',
    items=StringField(),
    default=['cyberchef', 'renderfindings', 'scanimport'],
    required=False,
    extra_info={
        'group': 'plugins',
        'professional_only': False,
        'load_from_env': Csv(post_process=lambda lst: list(filter(None, lst or []))),
    },
    help_text='List of enabled plugin names or plugin IDs.',
)


class PluginConfig(AppConfig):
    """
    Plugins are similar to Django apps but provide additional SysReptor-specific functionality.
    For basics on Django apps see: https://docs.djangoproject.com/en/stable/ref/applications/
    """

    plugin_id: str = None
    """
    Unique plugin identifier, that never changes.
    It's recommended to use a UUID (`python3 -m uuid`).
    The plugin_id is used internally to uniquely identify the plugin and it's resources (e.g. DB tables, API endpoints, etc.).
    """

    professional_only: bool = False
    """
    Indicates whether the plugin is only available in SysReptor professional or also in SysReptor community edition.
    """

    configuration_definition: FieldDefinition|None = None
    """
    Definition of the plugin's configurations. Settings are loaded from env variables or from the database and can be edited via the settings page in the UI.
    """

    def __init__(self, *args, **kwargs) -> None:
        if not self.plugin_id:
            raise ImproperlyConfigured('PluginConfig must have a plugin_id attribute')

        super().__init__(*args, **kwargs)
        enabled_plugins.append(self)

    @classproperty
    def label(cls) -> str:
        """
        Django app label used to identify the app internally
        """
        if not cls.plugin_id:
            return None
        return f'plugin_{cls.plugin_id.replace("-", "").replace("/", "")}'

    @property
    def urlpatterns(self) -> list:
        """
        Return the urlpatterns defined in the plugin's urls.py file.
        """
        if not module_has_submodule(self.module, 'urls'):
            return []
        urls_module = import_module(f'{self.name}.urls')
        if not hasattr(urls_module, 'urlpatterns'):
            return []
        return urls_module.urlpatterns

    @property
    def websocket_urlpatterns(self) -> list:
        if not module_has_submodule(self.module, 'urls'):
            return []
        urls_module = import_module(f'{self.name}.urls')
        if not hasattr(urls_module, 'websocket_urlpatterns'):
            return []
        return urls_module.websocket_urlpatterns

    def get_frontend_entry(self, request) -> str|None:
        return self._frontend_entry

    @cached_property
    def _frontend_entry(self) -> str|None:
        try:
            path = f'plugins/{self.plugin_id}/plugin.js'
            if finders.find(path):
                return storages['staticfiles'].url(path)
        except ValueError:
            pass
        return None

    def get_frontend_settings(self, request) -> dict:
        """
        Return a dictionary with settings passed to the plugin's frontend implementation.
        Settings are fetched during initial loading of the web interface.
        The user might not yet be authenticated at this point.
        If you need user-specific settings, implement a custom API endpoint.
        """
        return {}


class AppDirectoriesFinderWithoutPluginApps(AppDirectoriesFinder):
    def __init__(self, app_names=None, *args, **kwargs):
        if not app_names:
            app_names = [a.name for a in apps.get_app_configs() if not isinstance(a, PluginConfig)]
        super().__init__(*args, app_names=app_names, **kwargs)


class PluginDirectoriesFinder(FileSystemFinder):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.locations = []
        self.storages = {}
        for plugin in enabled_plugins:
            prefix = f'plugins/{plugin.plugin_id}'
            path = (Path(plugin.path) / 'static').resolve()
            if path.is_dir():
                self.locations.append((prefix, str(path)))
                storage = FileSystemStorage(location=path)
                storage.prefix = prefix
                self.storages[str(path)] = storage


class SysreptorPluginsLoader:
    """Loader for the virtual ``sysreptor_plugins`` package (no on-disk package tree)."""

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        pass


class SysreptorPluginsFinder:
    """
    Meta path finder that exposes PLUGIN_DIRS as the virtual package ``sysreptor_plugins``.
    Submodules (e.g. ``sysreptor_plugins.demoplugin``) resolve via the normal path-based
    importer against those directories.
    """

    def __init__(self, plugin_dirs: list[Path]):
        self.plugin_dirs = [str(p) for p in plugin_dirs if p.is_dir()]

    def find_spec(self, fullname, path, target=None):
        if fullname != SYSREPTOR_PLUGINS_PACKAGE:
            return None
        if not self.plugin_dirs:
            return None
        # Point origin at PLUGIN_DIRS[0]/__init__.py so the collection root is that directory
        # (the file need not exist; only the parent directory must).
        origin = str(Path(self.plugin_dirs[0]) / '__init__.py')
        spec = ModuleSpec(
            SYSREPTOR_PLUGINS_PACKAGE,
            SysreptorPluginsLoader(),
            origin=origin,
            is_package=True,
        )
        spec.submodule_search_locations = list(self.plugin_dirs)
        return spec


class _PluginAliasLoader:
    """Loader that returns the already-named ``sysreptor_plugins.*`` module object."""

    def __init__(self, real_name: str):
        self.real_name = real_name

    def create_module(self, spec):
        return import_module(self.real_name)

    def exec_module(self, module):
        pass


class SysreptorPluginAliasFinder:
    """
    Map top-level plugin module names (e.g. ``demoplugin``) to ``sysreptor_plugins.*``.

    Pytest collects plugin tests from PLUGIN_DIRS as top-level packages because those
    paths sit outside the api rootdir. Aliasing keeps relative imports and Django models
    resolving to the same modules registered in INSTALLED_APPS.
    """

    def __init__(self, plugin_module_names: set[str]):
        self.plugin_module_names = plugin_module_names

    def find_spec(self, fullname, path, target=None):
        root = fullname.split('.', 1)[0]
        if root not in self.plugin_module_names:
            return None
        real_name = f'{SYSREPTOR_PLUGINS_PACKAGE}.{fullname}'
        try:
            real_spec = importlib.util.find_spec(real_name)
        except (ImportError, ModuleNotFoundError, ValueError):
            return None
        if real_spec is None:
            return None

        is_package = real_spec.submodule_search_locations is not None
        spec = ModuleSpec(fullname, _PluginAliasLoader(real_name), is_package=is_package)
        if is_package:
            spec.submodule_search_locations = list(real_spec.submodule_search_locations)
        return spec


def iter_plugin_module_dirs(plugin_dirs: list[Path]):
    seen: dict[str, Path] = {}
    for plugins_dir in plugin_dirs:
        if not plugins_dir.is_dir():
            continue
        for module_dir in sorted(list(plugins_dir.iterdir())):
            existing = seen.get(module_dir.name)
            if existing is not None and existing != module_dir:
                raise ImproperlyConfigured(f'Duplicate plugin module: {module_dir.name}')
            seen[module_dir.name] = module_dir
            yield module_dir


def install_sysreptor_plugins_finder(plugin_dirs: list[Path]) -> SysreptorPluginsFinder:
    """
    Register (or replace) the meta path finders for ``sysreptor_plugins``.
    Validates duplicate module names across PLUGIN_DIRS before installing.
    """
    module_dirs = list(iter_plugin_module_dirs(plugin_dirs))
    plugin_module_names = {d.name for d in module_dirs}

    finder = SysreptorPluginsFinder(plugin_dirs)
    alias_finder = SysreptorPluginAliasFinder(plugin_module_names)

    # Idempotent: replace any prior finders (e.g. when load_plugins is called again in tests).
    sys.meta_path[:] = [
        f for f in sys.meta_path
        if not isinstance(f, SysreptorPluginsFinder | SysreptorPluginAliasFinder)
    ]
    # Alias finder after the namespace finder so ``sysreptor_plugins`` resolves first.
    sys.meta_path.insert(0, finder)
    sys.meta_path.insert(1, alias_finder)

    # Drop a previously loaded package so re-install picks up updated PLUGIN_DIRS.
    if SYSREPTOR_PLUGINS_PACKAGE in sys.modules:
        del sys.modules[SYSREPTOR_PLUGINS_PACKAGE]
    for name in list(sys.modules):
        if name in plugin_module_names or name.split('.', 1)[0] in plugin_module_names:
            # Only drop top-level aliases, not sysreptor_plugins.* (except parent above)
            if not name.startswith(SYSREPTOR_PLUGINS_PACKAGE):
                del sys.modules[name]

    return finder


def read_enabled_plugins_from_db(databases: dict) -> str | None:
    if not databases.get('default', {}).get('HOST'):
        return None

    # Use a dedicated connection handler without the psycopg pool to avoid interfering
    # with Django's default connection (especially during early settings import).
    databases = deepcopy(databases)
    databases.get('default', {}).get('OPTIONS', {}).pop('pool', None)
    connections = ConnectionHandler(databases)
    # Django blocks sync DB operations when an event loop is running (e.g. uvicorn subprocess startup).
    with mock.patch.dict(os.environ, {'DJANGO_ALLOW_ASYNC_UNSAFE': 'true'}):
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    'ignore',
                    message=re.escape(CursorWrapper.APPS_NOT_READY_WARNING_MSG),
                    category=RuntimeWarning,
                )
                with connections['default'].cursor() as cursor:
                    cursor.execute(
                        'SELECT value FROM api_utils_dbconfigurationentry WHERE name = %s LIMIT 1',
                        ['ENABLED_PLUGINS'],
                    )
                    row = cursor.fetchone()
                    if row is None:
                        return None
                    return row[0]
        except Exception:
            logging.error('Failed to read ENABLED_PLUGINS from database during startup')
            return None
        finally:
            connections.close_all()


def resolve_enabled_plugins(
    databases: dict | None = None,
    *,
    load_configurations_from_env: bool = True,
    load_configurations_from_db: bool = True,
) -> list[str]:
    cfg = Configuration()
    value = None
    if ENABLED_PLUGINS_FIELD.id in Configuration._force_override:
        value = Configuration._force_override[ENABLED_PLUGINS_FIELD.id]
    elif load_configurations_from_env and 'ENABLED_PLUGINS' in os.environ:
        value = cfg._load_env_value(ENABLED_PLUGINS_FIELD, os.environ['ENABLED_PLUGINS'])
    elif load_configurations_from_db and databases:
        value = cfg._decode_json_value(read_enabled_plugins_from_db(databases))
    return cfg._validate_configuration_value(ENABLED_PLUGINS_FIELD, value) or []


def load_all_plugins() -> bool:
    return len(sys.argv) >= 2 and Path(sys.argv[0]).name == 'manage.py' and sys.argv[1] in {
        # Commands that should load all plugins into INSTALLED_APPS (even if not enabled at runtime).
        # This is primarily needed for migrations, static file collection, and backups/restores.
        'collectstatic', 'findstatic',
        'makemigrations', 'migrate', 'optimizemigrations', 'showmigrations', 'squashmigrations', 'sqlflush', 'sqlmigrate', 'sqlsequencereset',
        'check', 'spectacular',
        'backup', 'restorebackup',
    }


def can_load_professional_plugins(license_text: str | None = None):
    license_text = license_text or getattr(settings, 'LICENSE', None) or config('LICENSE', default=None)
    if license.decode_and_validate_license(license=license_text, skip_db_checks=True) \
        .get('type') == license.LicenseType.PROFESSIONAL:
        return True
    elif load_all_plugins():
        return True
    return False


def load_plugins(settings):
    plugin_dirs = settings['PLUGIN_DIRS']
    try:
        install_sysreptor_plugins_finder(plugin_dirs)
    except Exception:
        logging.exception('Error while installing plugin import finder')
        return []

    if not any(d.is_dir() for d in plugin_dirs):
        return []

    # Check plugin modules and get plugin config classes
    available_plugin_configs = []
    for module_dir in iter_plugin_module_dirs(plugin_dirs):
        init_file = module_dir / '__init__.py'
        apps_file = module_dir / 'apps.py'
        if not init_file.is_file() or not apps_file.is_file():
            continue

        module_name = f'{SYSREPTOR_PLUGINS_PACKAGE}.{module_dir.name}'
        try:
            plugin_app_module = import_module(module_name + '.apps')
        except ImportError:
            continue
        plugin_config_class = next(filter(lambda c: issubclass(c, PluginConfig) and c != PluginConfig, map(lambda c: getattr(plugin_app_module, c), dir(plugin_app_module))), None)
        if not plugin_config_class:
            continue

        if not plugin_config_class.plugin_id or not isinstance(plugin_config_class.plugin_id, str):
            logging.warning(f'PluginConfig "{plugin_config_class.__name__}" must have a valid plugin_id')
            continue

        plugin_config_class.name = module_name
        if any(c.plugin_id == plugin_config_class.plugin_id for c in available_plugin_configs):
            logging.warning(f'Duplicate plugin_id: {plugin_config_class.plugin_id}')
            continue

        available_plugin_configs.append(plugin_config_class)
    available_plugins.clear()
    available_plugins.extend(available_plugin_configs)

    # Determine enabled plugins
    enabled_plugin_ids = resolve_enabled_plugins(
        databases=settings['DATABASES'],
        load_configurations_from_env=settings['LOAD_CONFIGURATIONS_FROM_ENV'],
        load_configurations_from_db=settings['LOAD_CONFIGURATIONS_FROM_DB'],
    )
    if load_all_plugins():
        enabled_plugin_ids += ['*']

    installed_apps = []
    for enabled_plugin_id in enabled_plugin_ids:
        matched = False
        for plugin_config_class in available_plugin_configs:
            plugin_id = plugin_config_class.plugin_id
            plugin_name = plugin_config_class.name.split('.')[-1]
            if enabled_plugin_id not in [plugin_id, plugin_name, '*']:
                continue

            matched = True
            app_class = plugin_config_class.__module__ + '.' + plugin_config_class.__name__
            app_label = plugin_config_class.label

            if plugin_config_class.professional_only and not can_load_professional_plugins(settings['LICENSE']):
                logging.info(f'Plugin "{plugin_name}" requires a professional license. Not enabling plugin.')
            elif app_class not in installed_apps:
                installed_apps.append(app_class)
                logging.info(f'Enabling plugin {plugin_name} ({plugin_id=}, {app_label=}, {app_class=})')

            if enabled_plugin_id != '*':
                # Specific IDs match at most one plugin, skip iteration if we found a match
                # '*' matches all plugins, so we need to continue iterating to check all plugins
                break
        if not matched and enabled_plugin_id != '*':
            logging.info(f'Plugin "{enabled_plugin_id}" not found in plugins')

    return installed_apps
