
import pytest
from django.http import FileResponse, StreamingHttpResponse
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone
from rest_framework.settings import api_settings

from sysreptor.pentests import views
from sysreptor.tests.mock import (
    api_client,
    api_client_with_token,
    create_project,
    create_project_api_token,
    create_project_type,
    create_template,
    create_user,
    update,
)
from sysreptor.tests.test_api import (
    ApiRequestsAndPermissionsTestData,
    admin_urls,
    api_requests_mock_configuration,
    expect_result,
    project_viewset_urls,
    projecttype_viewset_urls,
    template_urls,
    user_viewset_urls,
    viewset_urls,
)
from sysreptor.users.auth import ProjectAPITokenAuthentication
from sysreptor.users.roles import Permission


def without_design_copy(urls):
    return [u for u in urls if 'copy' not in u[0]]


def without_fromtemplate(urls):
    return [u for u in urls if 'fromtemplate' not in u[0]]


def project_token_read_urls():
    return [
        ('publicutils-settings', lambda s, c: c.get(reverse('publicutils-settings'))),
        *project_viewset_urls(get_obj=lambda s: s.project, list=True, read=True),
        *without_design_copy(projecttype_viewset_urls(get_obj=lambda s: s.project_type_customized, list=True, read=True)),
    ]


def project_token_write_urls():
    return [
        *without_fromtemplate(project_viewset_urls(get_obj=lambda s: s.project, write=True, update=False, destroy=False, create=False, share=False)),
    ]


def project_token_forbidden_urls():
    return [
        # Project administration
        *project_viewset_urls(get_obj=lambda s: s.project, create=True, update=True, destroy=True, write=False, share=True),
        ('pentestproject customize-projecttype', lambda s, c: c.post(reverse('pentestproject-customize-projecttype', kwargs={'pk': s.project.pk}), data={'project_type': s.project.project_type.id})),
        ('pentestproject archive-check', lambda s, c: c.get(reverse('pentestproject-archive-check', kwargs={'pk': s.project_readonly.pk}))),
        ('pentestproject archive', lambda s, c: c.post(reverse('pentestproject-archive', kwargs={'pk': s.project_readonly.pk}))),

        # Project not included in project token
        *project_viewset_urls(get_obj=lambda s: s.project_readonly, read=True, write=True),

        # Unrelated API endpoints
        *viewset_urls('pentestuser', get_kwargs=lambda s, detail: {'pk': 'self'}, retrieve=True, update=True, update_partial=True, destroy=True),
        *viewset_urls('pentestuser', get_kwargs=lambda s, detail: {}, list=True),
        *viewset_urls('findingtemplate', get_kwargs=lambda s, detail: {'pk': s.template.pk} if detail else {}, list=True, retrieve=True),
        *viewset_urls('archivedproject', get_kwargs=lambda s, detail: {'pk': s.archived_project.pk} if detail else {}, list=True, retrieve=True),

        *template_urls(create=True, edit=True, destroy=True, import_=True, export=True),
        *projecttype_viewset_urls(get_obj=lambda s: s.project_type, write=True, destroy=True, create_global=True, import_global=True, export=True),
        *user_viewset_urls(get_kwargs=lambda s, detail: {'pk': s.user_other.pk} if detail else {}, create=True, update=True, update_partial=True, destroy=True),
        *project_viewset_urls(get_obj=lambda s: s.project_unauthorized, read=True, write=True),
        *admin_urls(),
    ]


def project_token_out_of_scope_urls():
    return [
        *project_viewset_urls(get_obj=lambda s: s.project_unauthorized, read=True),
        *without_design_copy(projecttype_viewset_urls(get_obj=lambda s: s.project_unauthorized.project_type, read=True)),
    ]


def build_project_token_parameters():
    yield from expect_result(
        urls=project_token_read_urls(),
        allowed_users=['project_token_ro', 'project_token_rw'],
        forbidden_users=[],
    )
    yield from expect_result(
        urls=project_token_write_urls(),
        allowed_users=['project_token_rw'],
        forbidden_users=['project_token_ro'],
    )
    yield from expect_result(
        urls=project_token_forbidden_urls(),
        allowed_users=[],
        forbidden_users=['project_token_ro', 'project_token_rw'],
    )


@pytest.mark.django_db()
@api_requests_mock_configuration()
@pytest.mark.parametrize(('username', 'name', 'perform_request', 'options', 'expected'), sorted(build_project_token_parameters(), key=lambda t: (t[0], t[1], t[4])))
def test_project_token_api_requests(username, name, perform_request, options, expected):
    with api_requests_mock_configuration():
        user = ApiRequestsAndPermissionsTestData.create_user()
        update(user, is_superuser=True, roles=['regular_user', 'project_admin', 'designer', 'template_editor'])

        data = ApiRequestsAndPermissionsTestData(user)
        # Bind token to member projects exercised by the matrix (writable + finished).
        token = create_project_api_token(
            user=user,
            projects=[data.project],  # not project_readonly
            read_only=username == 'project_token_ro',
        )
        client = api_client_with_token(token)

        if initialize_dependencies := (options or {}).get('initialize_dependencies'):
            initialize_dependencies(data)
        res = perform_request(data, client)
        info = getattr(res, 'data', res.content) if not isinstance(res, FileResponse | StreamingHttpResponse) else res
        if expected:
            assert 200 <= res.status_code < 300, {'message': 'API request failed, but should have succeeded', 'info': info, 'name': name}
        else:
            assert 400 <= res.status_code < 500, {'message': 'API request succeeded, but should have failed', 'info': info, 'name': name}


@pytest.mark.django_db()
class TestProjectTokenAuthentication:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user()
        self.project = create_project(members=[self.user])
        self.token = create_project_api_token(self.user, [self.project], read_only=False)
        self.client_token = api_client_with_token(self.token)

    def test_project_api_token_authentication(self):
        assert self.client_token.get(reverse('pentestproject-detail', kwargs={'pk': self.project.id})).status_code == 200

    def test_default_authenticators_deny_project_token(self):
        assert views.UserNotebookPageViewSet.authentication_classes == api_settings.DEFAULT_AUTHENTICATION_CLASSES
        assert ProjectAPITokenAuthentication not in views.UserNotebookPageViewSet.authentication_classes
        assert self.client_token.get(reverse('pentestuser-detail', kwargs={'pk': 'self'})).status_code == 401

    def test_member_removed_from_project(self):
        self.project.members.all().delete()
        assert self.client_token.get(reverse('pentestproject-detail', kwargs={'pk': self.project.id})).status_code == 404

    def test_admin_permissions_dropped_from_user(self):
        update(self.user, roles=['regular_user', 'project_admin'], is_superuser=True)
        self.user.admin_permissions_enabled = True
        self.project.members.all().delete()
        assert self.client_token.get(reverse('pentestproject-detail', kwargs={'pk': self.project.id})).status_code == 404

    @pytest.mark.parametrize(('read_only', 'expected'), [
        (True, {Permission.PROJECT_READ}),
        (False, {Permission.PROJECT_READ, Permission.PROJECT_EDIT_CONTENT}),
    ])
    def test_effective_permissions_restricted(self, read_only, expected):
        update(self.user, roles=['regular_user', 'project_admin', 'template_editor', 'designer'], is_superuser=True)
        token = create_project_api_token(self.user, [self.project], read_only=read_only)
        request = RequestFactory().get('/')
        request.META['HTTP_AUTHORIZATION'] = f'Bearer {token.token_formatted}'
        user, _ = ProjectAPITokenAuthentication().authenticate(request)
        assert not user.is_admin
        assert set(user.effective_permissions) == {p.value for p in expected}
        for p in Permission:
            assert user.has_permission(p) == (p in expected)

    def test_delete_last_project_does_not_unrestrict(self):
        self.token.projects.all().delete()
        p = create_project(members=[self.user])
        assert self.client_token.get(reverse('pentestproject-detail', kwargs={'pk': p.id})).status_code == 404

    def test_list_views_filtered(self):
        create_project(members=[self.user])
        create_project(members=[])

        # Only allowed projects included in project token
        res_projects = self.client_token.get(reverse('pentestproject-list'))
        assert [p['id'] for p in res_projects.data['results']] == [str(self.project.id)]
        # No global designs (project tokens lack design.global.read); project-scoped designs only
        res_designs = self.client_token.get(reverse('projecttype-list'))
        assert res_designs.data['results'] == []
        assert self.client_token.get(reverse('projecttype-detail', kwargs={'pk': self.project.project_type_id})).status_code == 404
        # No templates
        assert self.client_token.get(reverse('findingtemplate-list')).status_code == 401

    def test_nested_and_bulk_references_cannot_escape_scope(self):
        other = create_project(members=[self.user])
        project_type = create_project_type()
        template = create_template()
        assert self.client_token.get(reverse('finding-detail', kwargs={'project_pk': other.id, 'id': other.findings.first().finding_id})).status_code == 404
        # Project export requires project.export (not granted to project tokens).
        assert self.client_token.post(reverse('pentestproject-export-bulk'), {'ids': [str(self.project.id), str(other.id)]}).status_code == 403
        # Out-of-scope design filtered by only_permitted → serializer validation error.
        assert self.client_token.post(reverse('projecttype-export-bulk'), {'ids': [str(project_type.id)]}).status_code == 400
        assert self.client_token.post(reverse('findingtemplate-export-bulk'), {'ids': [str(template.id)]}).status_code == 401

    @pytest.mark.parametrize(('expected', 'data'), [
        (True, {}),
        (True, {'projects': []}),
        (True, {'projects': [], 'read_only': False}),
        (True, {'projects': [], 'admin_permissions_enabled': True}),
        (False, {'projects': [], 'read_only': True}),
        (True, {'projects': ['member'], 'read_only': False}),
        (True, {'projects': ['member'], 'read_only': True}),
        (False, {'projects': ['other']}),
        (False, {'projects': ['member'], 'admin_permissions_enabled': True}),
    ])
    def test_create_project_token_validation(self, expected, data):
        projects = {
            'member': create_project(members=[self.user]),
            'other': create_project(members=[]),
        }
        update(self.user, is_superuser=True, admin_permissions_enabled=True)
        client = api_client(self.user)
        session = client.session
        session['authentication_info'] = {
            'login_time': timezone.now().isoformat(),
            'reauth_time': timezone.now().isoformat(),
        }
        session.save()
        res = client.post(reverse('apitoken-list', kwargs={'pentestuser_pk': 'self'}), data=data | {
            'projects': [{'id': str(projects[p].id)} for p in data.get('projects', [])],
        })
        assert res.status_code == (201 if expected else 400)
