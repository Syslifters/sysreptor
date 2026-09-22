from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace
from unittest import mock
from uuid import uuid4

import pytest
from django.db import IntegrityError, transaction
from django.urls import resolve
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIRequestFactory

from sysreptor.audit.models import AuditLogEntry, AuditLogTypes
from sysreptor.pentests import views
from sysreptor.pentests.models import PentestProject, ProjectType
from sysreptor.pentests.rendering.render_utils import RenderStageResult
from sysreptor.tests.mock import (
    api_client,
    create_project,
    create_template,
    create_user,
    override_configuration,
    update,
)
from sysreptor.users.models import APIToken, PentestUser
from sysreptor.users.serializers import APITokenCreateSerializer
from sysreptor.users.token_permissions import check_project_token_permissions, project_token_actions


class TestProjectTokenAllowlist:
    @pytest.mark.parametrize(('view_class', 'action', 'method'), [
        (views.PentestProjectViewSet, 'new_read_action', 'GET'),
        (views.PentestProjectViewSet, 'create', 'POST'),
        (views.PentestProjectViewSet, 'retrieve', 'POST'),
        (views.PentestProjectViewSet, 'metadata', 'OPTIONS'),
        (views.PentestProjectViewSet, 'partial_update', 'PATCH'),
        (views.PentestProjectViewSet, 'readonly', 'PATCH'),
        (views.PentestProjectViewSet, 'destroy', 'DELETE'),
        (views.PentestProjectViewSet, 'archive', 'POST'),
        (views.PentestProjectViewSet, 'copy', 'POST'),
        (views.PentestFindingViewSet, 'fromtemplate', 'POST'),
        (views.ProjectNoteShareInfoViewSet, 'list', 'GET'),
        (views.ProjectTypeViewSet, 'list', 'GET'),
        (views.FindingTemplateViewSet, 'create', 'POST'),
        (views.UserNotebookPageViewSet, 'list', 'GET'),
        (type('PluginProjectView', (views.PentestProjectViewSet,), {}), 'retrieve', 'GET'),
        (type('NewView', (), {}), 'list', 'GET'),
    ])
    @pytest.mark.parametrize('read_only', [True, False])
    def test_unlisted_capabilities_denied(self, view_class, action, method, read_only):
        view = view_class()
        view.action = action
        request = SimpleNamespace(parser_context={'view': view}, method=method)
        with pytest.raises(PermissionDenied):
            check_project_token_permissions(request, SimpleNamespace(read_only=read_only))

    def test_every_listed_capability_and_write_boundary(self):
        read, write = project_token_actions()
        assert read.isdisjoint(write)
        for view_class, action, method in read | write:
            view = view_class()
            view.action = action
            request = SimpleNamespace(parser_context={'view': view}, method=method)
            check_project_token_permissions(request, SimpleNamespace(read_only=False))
            if (view_class, action, method) in read:
                check_project_token_permissions(request, SimpleNamespace(read_only=True))
            else:
                with pytest.raises(PermissionDenied):
                    check_project_token_permissions(request, SimpleNamespace(read_only=True))

    def test_missing_view_denied(self):
        with pytest.raises(PermissionDenied):
            check_project_token_permissions(SimpleNamespace(parser_context={}, method='GET'), SimpleNamespace(read_only=False))


@pytest.mark.django_db()
class TestProjectTokens:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user()
        self.project = create_project(members=[self.user])
        self.second = create_project(members=[self.user])
        self.outside = create_project(members=[self.user])
        self.token = APIToken.objects.create(user=self.user, is_project_restricted=True, read_only=False)
        self.token.projects.set([self.project, self.second])
        self.client = api_client()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token.token_formatted)
        self.base = f'/api/v1/pentestprojects/{self.project.id}/'

    def serializer(self, **data):
        request = APIRequestFactory().post('/api/v1/pentestusers/self/apitokens/')
        request.user = self.user
        return APITokenCreateSerializer(data=data, context={'user': self.user, 'request': request})

    def test_project_and_design_visibility(self):
        assert {p['id'] for p in self.client.get('/api/v1/pentestprojects/').data['results']} == {str(self.project.id), str(self.second.id)}
        for project, status in [(self.project, 200), (self.second, 200), (self.outside, 404)]:
            assert self.client.get(f'/api/v1/pentestprojects/{project.id}/').status_code == status
            assert self.client.get(f'/api/v1/projecttypes/{project.project_type_id}/').status_code == status
            assert self.client.get(f'/api/v1/projecttypes/{project.project_type_id}/assets/').status_code == status
            for resource in ['notes', 'findings', 'sections', 'images', 'files', 'comments']:
                assert self.client.get(f'/api/v1/pentestprojects/{project.id}/{resource}/').status_code == status

    @pytest.mark.parametrize('role', ['member', 'guest', 'project_admin', 'admin'])
    def test_only_permitted_enforces_scope_before_privileged_returns(self, role):
        user = PentestUser.objects.get(pk=self.user.pk)
        user.is_guest = role == 'guest'
        user.is_project_admin = role == 'project_admin'
        user.is_superuser = role == 'admin'
        user.admin_permissions_enabled = role == 'admin'
        user.api_token = self.token
        assert set(PentestProject.objects.only_permitted(user)) == {self.project, self.second}
        assert set(ProjectType.objects.only_permitted(user)) == {self.project.project_type, self.second.project_type}

    def test_membership_loss_is_intersected_each_request(self):
        self.project.members.all().delete()
        assert self.client.get(self.base).status_code == 404
        assert self.client.get(f'/api/v1/projecttypes/{self.project.project_type_id}/').status_code == 404
        assert self.client.get(f'/api/v1/pentestprojects/{self.second.id}/').status_code == 200

    def test_project_admin_still_scoped_without_membership(self):
        update(self.user, is_project_admin=True)
        self.project.members.all().delete()
        assert self.client.get(self.base).status_code == 200
        assert self.client.get(f'/api/v1/pentestprojects/{self.outside.id}/').status_code == 404

    def test_deleting_last_project_does_not_unrestrict(self):
        self.project.delete()
        self.second.delete()
        self.token.refresh_from_db()
        assert self.token.is_project_restricted
        assert not self.token.projects.exists()
        assert self.client.get('/api/v1/pentestprojects/').data['results'] == []
        assert self.client.get(f'/api/v1/pentestprojects/{self.outside.id}/').status_code == 404

    @pytest.mark.parametrize('path', [
        '/api/v1/pentestusers/self/', '/api/v1/pentestusers/self/apitokens/',
        '/api/v1/pentestusers/self/notes/', '/api/v1/projecttypes/',
        '/api/v1/archivedprojects/', '/api/v1/utils/configuration/', '/api/v1/utils/chat/',
    ])
    def test_unrelated_endpoints_denied(self, path):
        assert self.client.get(path).status_code == 403

    def test_method_and_action_denial_on_real_routes(self):
        assert self.client.post('/api/v1/pentestprojects/', {}).status_code == 403
        assert self.client.patch(self.base, {'name': 'forbidden'}).status_code == 403
        assert self.client.patch(self.base + 'readonly/', {'readonly': True}).status_code == 403
        assert self.client.post(self.base + 'copy/', {}).status_code == 403
        assert self.client.delete(self.base).status_code == 403
        assert self.client.options(self.base).status_code == 403
        assert self.client.head(self.base).status_code == 200

    def test_bearer_denial_does_not_fall_back_to_session(self):
        self.client.force_login(self.user)
        assert self.client.get('/api/v1/pentestusers/self/').status_code == 403
        assert self.client.get(f'/api/v1/pentestprojects/{self.outside.id}/').status_code == 404

    @pytest.mark.parametrize('read_only', [True, False])
    def test_mcp_read_requests_and_template_exception(self, read_only):
        update(self.token, read_only=read_only)
        template = create_template()
        for path in [
            self.base, f'/api/v1/projecttypes/{self.project.project_type_id}/',
            self.base + 'findings/', self.base + 'sections/', self.base + 'notes/',
            '/api/v1/findingtemplates/?search=', f'/api/v1/findingtemplates/{template.id}/',
        ]:
            assert self.client.get(path).status_code == 200
        assert self.client.post('/api/v1/findingtemplates/', {}).status_code == 403
        assert self.client.post(self.base + 'findings/fromtemplate/', {'template': str(template.id)}).status_code == 403

    @pytest.mark.parametrize('read_only', [True, False])
    def test_mcp_content_writes(self, read_only):
        update(self.token, read_only=read_only)
        finding = self.project.findings.first()
        finding_url = self.base + f'findings/{finding.finding_id}/'
        section = self.project.sections.get(section_id='other')
        note = self.project.notes.filter(type='text').first()
        cases = [
            ('post', self.base + 'findings/', {'data': {'title': 'MCP finding'}}, 201),
            ('patch', finding_url, {'data': {'title': 'Patched'}}, 200),
            ('patch', self.base + f'sections/{section.section_id}/', {'data': {'field_string': 'MCP report'}}, 200),
            ('post', self.base + 'notes/', {'title': 'MCP note', 'text': 'new'}, 201),
            # reptor writes complete notes using PUT, not PATCH.
            ('put', self.base + f'notes/{note.note_id}/', {'title': 'Renamed', 'text': 'MCP contents'}, 200),
            ('delete', finding_url, {}, 204),
        ]
        for method, path, data, status in cases:
            response = getattr(self.client, method)(path, data)
            assert response.status_code == (403 if read_only else status), response.data

    def test_finished_project_and_guest_write_protection(self):
        update(self.project, readonly=True)
        assert self.client.post(self.base + 'findings/', {'data': {'title': 'blocked'}}).status_code == 403
        update(self.project, readonly=False)
        update(self.user, is_guest=True)
        with override_configuration(GUEST_USERS_CAN_EDIT_PROJECTS=False):
            assert self.client.post(self.base + 'notes/', {'title': 'blocked'}).status_code == 403
            assert self.client.get(self.base + 'notes/').status_code == 200

    def test_nested_and_bulk_references_cannot_escape_scope(self):
        finding = self.outside.findings.first()
        note = self.outside.notes.first()
        assert self.client.get(self.base + f'findings/{finding.finding_id}/').status_code == 404
        assert self.client.post(self.base + 'notes/', {'title': 'bad parent', 'parent': str(note.note_id)}).status_code == 400
        assert self.client.post(self.base + 'notes/export/', {'ids': [str(note.note_id)]}).status_code == 400
        assert self.client.post('/api/v1/pentestprojects/export/', {'ids': [str(self.project.id), str(self.outside.id)]}).status_code == 400

    def test_read_only_exports_and_checks(self):
        update(self.token, read_only=True)
        assert self.client.get(self.base + 'check/').status_code == 200
        for path, data in [
            (self.base + 'export/', {'export_all': True}),
            ('/api/v1/pentestprojects/export/', {'ids': [str(self.project.id), str(self.second.id)]}),
            (self.base + 'notes/export/', {}),
        ]:
            response = self.client.post(path, data)
            assert response.status_code == 200

    @pytest.mark.parametrize('action', ['preview', 'generate', 'md2html', 'notes/export-pdf'])
    def test_read_only_rendering_posts(self, action):
        update(self.token, read_only=True)
        with mock.patch('sysreptor.pentests.views.render_pdf', new_callable=mock.AsyncMock) as render_pdf, \
             mock.patch('sysreptor.pentests.views.render_note_to_pdf', new_callable=mock.AsyncMock) as render_notes, \
             mock.patch('sysreptor.pentests.views.render_project_markdown_fields_to_html', new_callable=mock.AsyncMock) as render_markdown:
            render_pdf.return_value = RenderStageResult(pdf=b'%PDF-1.3')
            render_notes.return_value = RenderStageResult(pdf=b'%PDF-1.3')
            render_markdown.return_value = {'result': {'id': str(self.project.id)}}
            data = {'notes': [str(self.project.notes.first().note_id)]} if action == 'notes/export-pdf' else {}
            response = self.client.post(self.base + action + '/', data)
            assert response.status_code == 200
            assert render_pdf.called or render_notes.called or render_markdown.called

    def test_copy_does_not_copy_token_associations(self):
        copied = self.project.copy()
        assert not copied.api_tokens.exists()
        assert self.token.projects.filter(pk=self.project.pk).exists()

    def test_cannot_forge_restriction_state(self):
        serializer = self.serializer(projects=[str(self.project.id)], is_project_restricted=False)
        assert serializer.is_valid(), serializer.errors
        assert serializer.save().is_project_restricted

    @pytest.mark.parametrize('condition', ['expired', 'inactive', 'revoked', 'community'])
    def test_invalid_tokens_rejected(self, condition):
        if condition == 'expired':
            update(self.token, expire_date=timezone.now().date() - timedelta(days=1))
        elif condition == 'inactive':
            update(self.user, is_active=False)
        elif condition == 'revoked':
            self.token.delete()
        with mock.patch('sysreptor.users.auth.license.is_professional', return_value=condition != 'community'):
            assert self.client.get(self.base).status_code == 401

    @pytest.mark.parametrize(('now', 'expected'), [
        (datetime(2026, 1, 31, tzinfo=UTC), date(2026, 2, 28)),
        (datetime(2028, 1, 31, tzinfo=UTC), date(2028, 2, 29)),
        (datetime(2026, 12, 22, tzinfo=UTC), date(2027, 1, 22)),
    ])
    def test_creation_defaults_and_complete_audit(self, now, expected):
        with mock.patch('django.utils.timezone.now', return_value=now):
            serializer = self.serializer(name='Restricted', projects=[str(self.project.id), str(self.second.id)])
            assert serializer.is_valid(), serializer.errors
            token = serializer.save()
        assert token.expire_date == expected
        assert token.read_only
        assert token.is_project_restricted
        assert not token.admin_permissions_enabled
        assert set(token.projects.all()) == {self.project, self.second}
        assert serializer.data['token'] == token.token_formatted
        assert token.validate_token(token.token_plaintext)
        assert token.token_plaintext not in token.token_hash
        entry = next(e for e in AuditLogEntry.objects.filter(type=AuditLogTypes.API_TOKEN_CREATED, object_id=self.user.id)
                     if e.data['api_token']['id'] == str(token.id))
        assert set(entry.data['api_token']['projects']) == {str(self.project.id), str(self.second.id)}
        assert 'token_hash' not in entry.data['api_token']
        assert 'token' not in entry.data['api_token']

    @pytest.mark.parametrize('restricted', [True, False])
    def test_optional_expiration(self, restricted):
        serializer = self.serializer(projects=[str(self.project.id)] if restricted else [], expire_date=None)
        assert serializer.is_valid(), serializer.errors
        assert serializer.save().expire_date is None

    def test_unrestricted_default_preserved(self):
        serializer = self.serializer(name='Normal')
        assert serializer.is_valid(), serializer.errors
        token = serializer.save()
        assert token.expire_date is None
        assert not token.is_project_restricted
        assert not token.read_only

    @pytest.mark.parametrize('data', [
        {'projects': [], 'read_only': True},
        {'projects': [str(uuid4())]},
        {'expire_date': '2000-01-01'},
    ])
    def test_invalid_creation(self, data):
        serializer = self.serializer(**data)
        assert not serializer.is_valid()

    def test_admin_elevation_cannot_grant_token_project_access(self):
        inaccessible = create_project()
        update(self.user, is_superuser=True)
        self.user.admin_permissions_enabled = True
        assert not self.serializer(projects=[str(inaccessible.id)]).is_valid()
        assert not self.serializer(projects=[str(self.project.id)], admin_permissions_enabled=True).is_valid()
        with pytest.raises(IntegrityError), transaction.atomic():
            APIToken.objects.create(user=self.user, is_project_restricted=True, admin_permissions_enabled=True)

    def test_global_management_and_revoke_after_license_downgrade(self):
        client = api_client(self.user)
        normal = APIToken.objects.create(user=self.user)
        with mock.patch('sysreptor.users.permissions.check_sensitive_operation_timeout', return_value=True):
            response = client.get('/api/v1/pentestusers/self/apitokens/')
            assert response.status_code == 200
            assert {t['id'] for t in response.data} == {str(normal.id), str(self.token.id)}
            assert all('token' not in t and 'token_hash' not in t for t in response.data)
            restricted = next(t for t in response.data if t['is_project_restricted'])
            assert {p['id'] for p in restricted['project_details']} == {str(self.project.id), str(self.second.id)}
            with mock.patch('sysreptor.utils.license.is_professional', return_value=False):
                assert client.delete(f'/api/v1/pentestusers/self/apitokens/{self.token.id}/').status_code == 204
        assert self.client.get(self.base).status_code == 401

    def test_create_reauthentication_and_community_restriction(self):
        client = api_client(self.user)
        url = '/api/v1/pentestusers/self/apitokens/'
        data = {'name': 'Test', 'projects': [str(self.project.id)]}
        assert client.post(url, data).status_code == 403
        with mock.patch('sysreptor.users.permissions.check_sensitive_operation_timeout', return_value=True):
            assert client.post(url, data).status_code == 201
            with mock.patch('sysreptor.utils.license.is_professional', return_value=False):
                assert client.post(url, data).status_code == 403

    def test_no_restricted_secret_after_refetch(self):
        assert APIToken.objects.get(pk=self.token.pk).token_formatted is None

    def test_last_used_updated(self):
        assert self.token.last_used is None
        assert self.client.get(self.base).status_code == 200
        self.token.refresh_from_db()
        assert self.token.last_used is not None

    def test_actual_route_capabilities_for_mcp(self):
        for method, path in [
            ('GET', self.base), ('GET', f'/api/v1/projecttypes/{self.project.project_type_id}/'),
            ('GET', self.base + 'findings/'), ('POST', self.base + 'findings/'),
            ('PATCH', self.base + f'findings/{uuid4()}/'), ('DELETE', self.base + f'findings/{uuid4()}/'),
            ('GET', self.base + 'sections/'), ('PATCH', self.base + 'sections/other/'),
            ('GET', self.base + 'notes/'), ('POST', self.base + 'notes/'), ('PUT', self.base + f'notes/{uuid4()}/'),
            ('GET', '/api/v1/findingtemplates/'), ('GET', f'/api/v1/findingtemplates/{uuid4()}/'),
        ]:
            match = resolve(path)
            capability = (match.func.cls, match.func.actions[method.lower()], method)
            read, write = project_token_actions()
            assert capability in read | write
