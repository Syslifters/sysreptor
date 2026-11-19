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
def mock_jira_request(project_pages=None, bulk_result=None, calls=None):
    project_id = '00cb6224-9a41-48f8-a2c0-991b0fb376ca'
    if project_pages is None:
        project_pages = [{
            'startAt': 0,
            'maxResults': 100,
            'isLast': True,
            'values': [
                {'id': project_id, 'key': 'PROJECT', 'name': 'Test Project'},
            ],
        }]

    async def mock_jira_api(client, endpoint, json=None, params=None, **kwargs):
        if calls is not None:
            calls.append({
                'method': kwargs.get('method'),
                'endpoint': endpoint,
                'json': json,
                'files': kwargs.get('files'),
            })
        if endpoint == '/rest/api/3/project/search':
            start_at = (params or {}).get('startAt', 0)
            for page in project_pages:
                if page.get('startAt', 0) == start_at:
                    return page
            raise Exception(f'Unhandled project search startAt={start_at}')
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
            if bulk_result is not None:
                return bulk_result
            return {
                'issues': [{
                    'key': f'PROJECT-{i+1}',
                } for i in range(len(json['issueUpdates']))],
            }
        elif re.match(r'/rest/api/3/issue/[\w-]+/attachments', endpoint):
            return [{'id': '10001', 'filename': 'image.png'}]
        elif re.match(r'/rest/api/3/issue/[\w-]+$', endpoint) and kwargs.get('method') == 'PUT':
            return None
        else:
            raise Exception(f'Unhandled mock endpoint: {endpoint}')

    async def mock_jira_get_media_id(client, attachment_id):
        return '12345678-1234-1234-1234-123456789abc'

    with mock.patch('sysreptor_plugins.jira.views.jira_request', new=mock_jira_api) as m, \
         mock.patch('sysreptor_plugins.jira.views.jira_get_media_id', new=mock_jira_get_media_id):
        yield m


@pytest.mark.django_db
class TestJiraAPI:
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
            'guest': create_user(roles=['guest']),
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

    def test_projects_pagination(self):
        user = create_user(is_superuser=True, admin_permissions_enabled=True)
        project = create_project(members=[user])
        client = api_client(user)

        project_pages = [
            {
                'startAt': 0,
                'maxResults': 100,
                'isLast': False,
                'values': [
                    {'id': '1', 'key': 'AAA', 'name': 'Project A'},
                    {'id': '2', 'key': 'BBB', 'name': 'Project B'},
                ],
            },
            {
                'startAt': 2,
                'maxResults': 100,
                'isLast': True,
                'values': [
                    {'id': '3', 'key': 'ZZZ', 'name': 'Project Z'},
                ],
            },
        ]

        with mock_jira_request(project_pages=project_pages):
            res = client.get(reverse(f'{URL_NAMESPACE}:jira-projects', kwargs={'project_pk': project.id}))

        assert res.status_code == 200
        assert res.data['projects'] == [
            {'id': '1', 'key': 'AAA', 'name': 'Project A'},
            {'id': '2', 'key': 'BBB', 'name': 'Project B'},
            {'id': '3', 'key': 'ZZZ', 'name': 'Project Z'},
        ]

    def test_bulk_partial_failure_keeps_images_on_the_created_issue(self):
        user = create_user(is_superuser=True, admin_permissions_enabled=True)
        project = create_project(
            members=[user],
            findings_kwargs=[{}, {}, {}],
            images_kwargs=[{'name': 'a.png'}, {'name': 'b.png'}, {'name': 'c.png'}],
        )
        findings = list(project.findings.order_by('created'))
        finding_a, finding_b, finding_c = findings

        def image_for(prefix):
            # Upload may keep the name or append a random suffix: a.png or a-<random>.png
            matches = [img for img in project.images.all() if img.name == f'{prefix}.png' or img.name.startswith(f'{prefix}-')]
            assert len(matches) == 1, [img.name for img in project.images.all()]
            return matches[0]

        images = {prefix: image_for(prefix) for prefix in ('a', 'b', 'c')}

        def description(finding, image):
            return {
                'version': 1,
                'type': 'doc',
                'content': [
                    {'type': 'paragraph', 'content': [{'type': 'text', 'text': f'body-{finding.finding_id}'}]},
                    {'type': 'mediaSingle', 'attrs': {'layout': 'center'}, 'content': [
                        {'type': 'media', 'attrs': {'type': 'external', 'url': f'/images/name/{image.name}'}},
                    ]},
                ],
            }

        # B fails validation. Jira returns A and C only, in request order.
        calls = []
        bulk_result = {
            'issues': [
                {'key': 'PROJECT-1'},
                {'key': 'PROJECT-3'},
            ],
            'errors': [{
                'failedElementNumber': 1,
                'elementErrors': {'errorMessages': ['summary is invalid'], 'errors': {}},
            }],
        }
        client = api_client(user)
        with mock_jira_request(bulk_result=bulk_result, calls=calls), override_configuration(
            JIRA_URL='https://jira.example.com',
            JIRA_USERNAME='user',
            JIRA_API_TOKEN='token',  # noqa: S106
        ):
            res = client.post(reverse(f'{URL_NAMESPACE}:jira-export', kwargs={'project_pk': project.id}), data={
                'jira_project': 'PROJECT',
                'issue_type': 'Bug',
                'issues': [
                    {'finding': finding_a.finding_id, 'summary': 'A', 'description': description(finding_a, images['a'])},
                    {'finding': finding_b.finding_id, 'summary': 'B', 'description': description(finding_b, images['b'])},
                    {'finding': finding_c.finding_id, 'summary': 'C', 'description': description(finding_c, images['c'])},
                ],
            })

        assert res.status_code == 200, res.data
        assert [(str(item['finding']), item['jira_key']) for item in res.data['created']] == [
            (str(finding_a.finding_id), 'PROJECT-1'),
            (str(finding_c.finding_id), 'PROJECT-3'),
        ]
        assert [(str(item['finding']), item['error']) for item in res.data['failed']] == [
            (str(finding_b.finding_id), 'summary is invalid'),
        ]

        uploads = [
            (call['endpoint'], call['files']['file'][0])
            for call in calls
            if str(call['endpoint']).endswith('/attachments')
        ]
        assert uploads == [
            ('/rest/api/3/issue/PROJECT-1/attachments', images['a'].name),
            ('/rest/api/3/issue/PROJECT-3/attachments', images['c'].name),
        ]

        puts = {
            call['endpoint']: call['json']['fields']['description']
            for call in calls
            if call['method'] == 'PUT'
        }
        assert set(puts) == {'/rest/api/3/issue/PROJECT-1', '/rest/api/3/issue/PROJECT-3'}
        assert f'body-{finding_a.finding_id}' in str(puts['/rest/api/3/issue/PROJECT-1'])
        assert f'body-{finding_c.finding_id}' in str(puts['/rest/api/3/issue/PROJECT-3'])
        assert f'body-{finding_b.finding_id}' not in str(puts['/rest/api/3/issue/PROJECT-3'])
