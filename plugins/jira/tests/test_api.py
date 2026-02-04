import contextlib
import re
from unittest import mock

import pytest
from django.urls import reverse
from sysreptor.tests.mock import (
    api_client,
    create_project,
    create_user,
    override_configuration,
)

from ..apps import JiraExportPluginConfig

PLUGIN_ID = JiraExportPluginConfig.plugin_id
URL_NAMESPACE = JiraExportPluginConfig.label


@contextlib.contextmanager
def mock_jira_request():
    async def mock_jira_api(client, endpoint, json=None, **kwargs):
        project_id = '00cb6224-9a41-48f8-a2c0-991b0fb376ca'
        if endpoint == '/rest/api/3/project/search':
            return {
                'values': [
                    {'id': project_id, 'key': 'PROJECT', 'name': 'Test Project'},
                ]
            }
        elif endpoint == '/rest/api/3/project/PROJECT':
            return {
                'id': project_id,
                'key': 'PROJECT',
                'name': 'Test Project',
                'issueTypes': [
                    {'id': '10001', 'name': 'Bug'},
                    {'id': '10002', 'name': 'Task'},
                ],
            }
        elif endpoint == '/rest/api/3/search/jql':
            return {
                'issues': []
            }
        elif endpoint == '/rest/api/3/issue/bulk':
            return {
                'issues': [{
                    'key': f'PROJECT-{i+1}',
                } for i in range(len(json['issueUpdates']))],
            }
        elif re.match(r'/rest/api/3/issue/[\w-]+/attachments', endpoint):
            return {}
        else:
            raise Exception(f'Unhandled mock endpoint: {endpoint}')

    with mock.patch('sysreptor_plugins.jira.views.jira_request', new=mock_jira_api) as m:
        yield m


@pytest.mark.django_db
class TestJiraAPI:
    @pytest.fixture(autouse=True)
    def setUp(self):
        with override_configuration(
            GUEST_USERS_CAN_IMPORT_PROJECTS=False,
            GUEST_USERS_CAN_CREATE_PROJECTS=False,
            GUEST_USERS_CAN_DELETE_PROJECTS=False,
            GUEST_USERS_CAN_UPDATE_PROJECT_SETTINGS=False,
            GUEST_USERS_CAN_EDIT_PROJECTS=False,
            GUEST_USERS_CAN_SHARE_NOTES=False,
            GUEST_USERS_CAN_SEE_ALL_USERS=False,
        ):
            yield

    @pytest.mark.parametrize(('project', 'user', 'expected'), [
        ('project', 'admin', True),
        ('project', 'member', True),
        ('project', 'guest', False),
        ('project', 'other', False),
        ('project', 'anonymous', False),
        ('readonly', 'admin', True),
        ('readonly', 'member', True),
        ('readonly', 'guest', False),
    ])
    def test_permissions(self, project, user, expected):
        users = {
            'admin': create_user(is_superuser=True, admin_permissions_enabled=True),
            'member': create_user(),
            'guest': create_user(is_guest=True),
            'other': create_user(),
            'anonymous': None,
        }
        projects = {
            'project': create_project(members=[users['member']]),
            'readonly': create_project(members=[users['member']], readonly=True),
        }
        user = users[user]
        project = projects[project]

        client = api_client(user)
        with mock_jira_request():
            res1 = client.get(reverse(f'{URL_NAMESPACE}:jira-projects', kwargs={'project_pk': project.id}))
            assert (res1.status_code == 200) == expected

            res2 = client.get(reverse(f'{URL_NAMESPACE}:jira-issuetypes', kwargs={'project_pk': project.id}, query={'jira_project': 'PROJECT'}))
            assert (res2.status_code == 200) == expected

            res3 = client.post(reverse(f'{URL_NAMESPACE}:jira-export', kwargs={'project_pk': project.id}), data={
                'jira_project': 'PROJECT',
                'issue_type': 'Bug',
                'issues': [
                    {
                        'finding': project.findings.first().finding_id,
                        'summary': 'Test Issue',
                        'description': {'type': 'doc', 'version': 1, 'content': []},
                    }
                ],
            })
            assert (res3.status_code == 200) == expected
            if expected:
                assert len(res3.data['created']) == 1
                assert len(res3.data['failed']) == 0 
