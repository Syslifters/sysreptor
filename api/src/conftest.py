"""
Pytest configuration for SysReptor API and plugin tests.
"""

from pathlib import Path


def pytest_configure(config):
    """
    Collect plugin tests from PLUGIN_DIRS when running the full suite.

    Replaces discovery via the former ``sysreptor_plugins/`` symlink tree under api/src.
    Skip when the user already passed explicit collection paths (file, dir, or --pyargs).
    """
    rootdir = Path(config.rootpath).resolve()
    resolved_args = [Path(a).resolve() for a in config.args]
    # Bare ``pytest`` / ``pytest -n auto`` uses rootdir as the sole collection arg.
    if resolved_args != [rootdir]:
        return

    from django.conf import settings

    seen = set(resolved_args)
    for plugin_dir in getattr(settings, 'PLUGIN_DIRS', []):
        if not plugin_dir.is_dir():
            continue
        resolved = plugin_dir.resolve()
        if resolved not in seen:
            config.args.append(str(resolved))
            seen.add(resolved)
