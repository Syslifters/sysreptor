import importlib.util
import logging
import shutil
import sys
from functools import cached_property
from importlib import import_module
from pathlib import Path

from decouple import config
from django.apps import AppConfig, apps
from django.conf import settings
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.finders import AppDirectoriesFinder, FileSystemFinder
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage, storages
from django.utils.functional import classproperty
from django.utils.module_loading import module_has_submodule

from reportcreator_api.utils import license

enabled_plugins = []


class PluginConfig(AppConfig):
    """
    Plugins are similar to Django apps but provide additional SysReptor-specific functionality.
    For basics on Django apps see: https://docs.djangoproject.com/en/stable/ref/applications/
    """

    plugin_id: str = None
    """
    Unique plugin identifier, that never changes.
    It's recommended to use a UUID (`python3 -c 'import uuid; print(str(uuid.uuid4()))'`).
    The plugin_id is used internally to uniquely identify the plugin and it's resources (e.g. DB tables, API endpoints, etc.).
    """

    professional_only: bool = False
    """
    Indicates whether the plugin is only available in SysReptor professional or also in SysReptor community edition.
    """

    frontend_settings = {}

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
        Dictionary with settings passed to the plugin's frontend implementation
        """
        return self.frontend_settings


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


def load_module_from_dir(module_name: str, path: Path):
    """
    Load a module from a directory.
    Sets the module import directory such that sub-modules can be imported.
    """
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def remove_entry(path: Path):
    if not path.exists():
        return
    if path.is_dir() and not path.is_symlink():
        try:
            shutil.rmtree(path)
        except FileNotFoundError:
            pass  # ignore race condition errors when multiple worker processes start at the same time
    else:
        path.unlink(missing_ok=True)


def can_load_professional_plugins():
    license_text = getattr(settings, 'LICENSE', config('LICENSE', default=None))
    if license.decode_and_validate_license(license=license_text, skip_db_checks=True) \
        .get('type') == license.LicenseType.PROFESSIONAL:
        return True
    elif len(sys.argv) >= 2 and sys.argv[0] == 'manage.py' and sys.argv[1] in [
        'collectstatic', 'findstatic',
        'makemigrations', 'migrate', 'optimizemigrations', 'showmigrations', 'squashmigrations', 'sqlflush', 'sqlmigrate', 'sqlsequencereset',
        'check', 'spectacular',
    ]:
        return True
    return False


def collect_plugins(dst: Path, srcs: list[Path]):
    # Collect plugins from all plugin directories
    all_module_dirs = []
    for plugins_dir in srcs:
        if not plugins_dir.is_dir():
            continue
        for src_module in plugins_dir.iterdir():
            if not src_module.is_dir():
                continue
            for p in all_module_dirs:
                if p.name == src_module.name and p != src_module:
                    raise ImproperlyConfigured(f'Duplicate plugin module: {src_module.name}')
            all_module_dirs.append(src_module)

    # Create symlinks to srcs modules in dst directory
    dst.mkdir(exist_ok=True, parents=True)
    for src_module in all_module_dirs:
        dst_module = dst / src_module.name

        if dst_module.is_dir() and dst_module.is_symlink() and dst_module.resolve() == src_module.resolve():
            # Already the expected entry. Do nothing
            continue
        else:
            # Create symlink
            remove_entry(dst_module)
            try:
                dst_module.symlink_to(src_module.resolve())
            except FileExistsError:
                pass
    # Add __init__.py
    dst_init = dst / '__init__.py'
    if not dst_init.exists():
        dst_init.touch()

    # Delete outdated entries
    expected_names = [m.name for m in all_module_dirs] + ['__init__.py']
    for dst_module in dst.iterdir():
        if dst_module.name not in expected_names:
            remove_entry(dst_module)


def load_plugins(plugin_dirs: list[Path], enabled_plugins: list[str]):
    dst = Path(__file__).parent.parent.parent / 'sysreptor_plugins'
    # Collect all plugin modules in dst directory
    try:
        collect_plugins(
            dst=dst,
            srcs=plugin_dirs,
        )
    except Exception:
        logging.exception('Error while collecting plugins')

    if not dst.is_dir() or not (dst / '__init__.py').is_file():
        logging.warning(f'Cannot load plugins: Plugin directory "{dst}" not found')
        return []

    # Load sysreptor_plugins module from dst directory
    load_module_from_dir('sysreptor_plugins', dst / '__init__.py')

    # Check plugin modules and get plugin config classes
    available_plugin_configs = []
    for module_dir in dst.iterdir():
        if not module_dir.is_dir():
            continue

        init_file = module_dir / '__init__.py'
        app_file = module_dir / 'app.py'
        if not init_file.is_file() or not app_file.is_file():
            continue

        module_name = f"sysreptor_plugins.{module_dir.name}"
        try:
            plugin_app_module = import_module(module_name + '.app')
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

    # Determine enabled plugins
    installed_apps = []
    for enabled_plugin_id in enabled_plugins:
        for plugin_config_class in available_plugin_configs:
            plugin_id = plugin_config_class.plugin_id
            plugin_name = plugin_config_class.name.split('.')[-1]
            if enabled_plugin_id in [plugin_id, plugin_name, '*']:
                # Add to installed_apps
                app_class = plugin_config_class.__module__ + '.' + plugin_config_class.__name__
                app_label = plugin_config_class.label

                if plugin_config_class.professional_only and not can_load_professional_plugins():
                    logging.warning(f'Plugin "{plugin_name}" requires a professional license. Not enabling plugin.')
                    continue
                if app_class not in installed_apps:
                    installed_apps.append(app_class)
                    logging.info(f'Enabling plugin {plugin_name} ({plugin_id=}, {app_label=}, {app_class=})')
                if enabled_plugin_id != '*':
                    break
        else:
            if enabled_plugin_id != '*':
                logging.warning(f'Plugin "{enabled_plugin_id}" not found in plugins')

    return installed_apps
