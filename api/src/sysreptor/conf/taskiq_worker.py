"""
Taskiq worker entrypoint.

Usage:
    taskiq worker sysreptor.conf.taskiq_worker:broker
"""

import os

import django
from django.utils.module_loading import autodiscover_modules

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sysreptor.conf.settings')
django.setup()

from sysreptor.conf.taskiq import broker  # noqa: E402

# Discover @broker.task definitions in all installed apps (incl. enabled plugins)
autodiscover_modules('tasks')
# Mail tasks live outside a Django app
import sysreptor.utils.mail  # noqa: E402, F401

__all__ = ['broker']
