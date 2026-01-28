"""
Unit tests for Jira Export plugin.

To run this test, execute:
cd sysreptor/dev
docker compose run --rm -e ENABLED_PLUGINS=jiraexport api pytest sysreptor_plugins/jiraexport
"""

import pytest
from django.urls import reverse
from sysreptor.tests.mock import (
    api_client,
    create_project,
    create_user,
)

from ..apps import JiraExportPluginConfig

PLUGIN_ID = JiraExportPluginConfig.plugin_id
URL_NAMESPACE = JiraExportPluginConfig.label


