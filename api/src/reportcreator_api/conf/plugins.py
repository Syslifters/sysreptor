import importlib.util
import logging
import sys
from importlib import import_module
from pathlib import Path

from django.apps import AppConfig, apps
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.finders import AppDirectoriesFinder, FileSystemFinder
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage, storages
from django.utils.module_loading import module_has_submodule

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

    def __init__(self, *args, **kwargs) -> None:
        if not self.plugin_id:
            raise ImproperlyConfigured('PluginConfig must have a plugin_id attribute')

        super().__init__(*args, **kwargs)
        enabled_plugins.append(self)

    @property
    def label(self) -> str:
        """
        Django app label used to identify the app internally
        """
        return f'plugin_{self.plugin_id.replace("-", "")}'

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
    def frontend_entry(self) -> str|None:
        path = f'plugins/{self.plugin_id}/plugin.js'
        if finders.find(path):
            return storages['staticfiles'].url(path)
        return None


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


def load_plugins(plugin_dirs: list[Path], enabled_plugins: list[str]):
    all_plugins_classes = []

    # Register top-level module
    sys.modules['sysreptor_plugins'] = {}
    # load_module_from_dir('sysreptor_plugins', Path(__file__).parent.parent / 'plugins' / '__init__.py')

    for plugins_dir in plugin_dirs:
        for module_dir in plugins_dir.iterdir():
            app_file = module_dir / 'app.py'
            if module_dir.is_dir() and app_file.is_file():
                try:
                    module_name = f"sysreptor_plugins.{module_dir.name}"
                    if any(c.name == module_name for c in all_plugins_classes):
                        raise ImproperlyConfigured(f'Duplicate plugin name: {module_name}')

                    load_module_from_dir(module_name, module_dir / '__init__.py')
                    plugin_module = import_module(module_name + '.app')
                    plugin_config_class = next(filter(lambda c: issubclass(c, PluginConfig), map(lambda c: getattr(plugin_module, c), dir(plugin_module))))
                    plugin_config_class.name = module_name
                    if any(c.plugin_id == plugin_config_class.plugin_id for c in all_plugins_classes):
                        raise ImproperlyConfigured(f'Duplicate plugin_id: {plugin_config_class.plugin_id}')

                    all_plugins_classes.append(plugin_config_class)
                except Exception:
                    logging.exception(f'Failed to load plugin from {module_dir}')

    out = []
    for plugin_id in enabled_plugins:
        for plugin_config_class in all_plugins_classes:
            if plugin_config_class.plugin_id == plugin_id or plugin_config_class.name.split('.')[-1] == plugin_id:
                out.append(plugin_config_class.__module__ + '.' + plugin_config_class.__name__)
                break
        else:
            logging.warning(f'Plugin "{plugin_id}" not found in plugins')
    return out


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
            path = Path(plugin.path) / 'static'
            if path.is_dir():
                self.locations.append((prefix, str(path)))
                storage = FileSystemStorage(location=path)
                storage.prefix = prefix
                self.storages[str(path)] = storage

