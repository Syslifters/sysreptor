import io
from uuid import uuid4
from django.urls import reverse
import pytest

from reportcreator_api.archive.import_export.import_export import export_project_types
from reportcreator_api.pentests.models import ProjectType, ProjectTypeScope, SourceEnum
from reportcreator_api.tests.mock import create_project, create_project_type, create_user, api_client


@pytest.mark.django_db
class TestProjectApi:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user()
        self.project_type = create_project_type()

        self.client = api_client(self.user) 

    def test_create_project(self):
        p = self.client.post(reverse('pentestproject-list'), data={
            'name': 'New Project',
            'project_type': self.project_type.id,
            'members': [],
        }).json()

        # User added as member
        assert len(p['members']) == 1
        assert p['members'][0]['id'] == str(self.user.id)

        # ProjectType copied on create
        assert p['project_type'] != str(self.project_type.id)
        assert self.client.get(reverse('projecttype-detail', kwargs={'pk': p['project_type']})).json()['source'] == SourceEnum.SNAPSHOT

    def test_copy_project(self):
        project = create_project(project_type=self.project_type, members=[self.user])
        cp = self.client.post(reverse('pentestproject-copy', kwargs={'pk': project.id})).json()
        assert cp['id'] != str(project.id)
        assert cp['project_type'] != str(project.project_type.id)
        assert cp['copy_of'] == str(project.id)
        pt = ProjectType.objects.get(id=cp['project_type'])
        assert pt.source == SourceEnum.SNAPSHOT
        assert str(pt.linked_project.id) == cp['id']

    def test_change_design(self):
        project = create_project(members=[self.user])
        project.project_type.linked_project = project
        project.project_type.save()

        # ProjectType not changed
        u = self.client.patch(reverse('pentestproject-detail', kwargs={'pk': project.id}), data={
            'project_type': project.project_type.id,
        }).json()
        assert u['project_type'] == str(project.project_type.id)

        # ProjectType changed
        p = self.client.patch(reverse('pentestproject-detail', kwargs={'pk': project.id}), data={
            'project_type': self.project_type.id
        }).json()

        assert p['project_type'] not in [str(project.project_type.id), str(self.project_type.id)]
        pt = ProjectType.objects.get(id=p['project_type'])
        assert pt.source == SourceEnum.SNAPSHOT
        assert pt.linked_project == project

    def test_change_imported_members(self):
        project = create_project(members=[self.user], imported_members=[{
            'id': uuid4(),
            'additional_field': 'test',
            'roles': [],
        }])
        res = self.client.patch(reverse('pentestproject-detail', kwargs={'pk': project.id}), data={
            'imported_members': [{'id': project.imported_members[0]['id'], 'roles': ['pentester']}]
        })
        assert res.status_code == 200
        project.refresh_from_db()
        assert project.imported_members[0]['roles'] == ['pentester']
        assert project.imported_members[0]['additional_field'] == 'test'


@pytest.mark.django_db
class TestProjectTypeApi:
    @pytest.mark.parametrize('user,scope,expected', [
        ('designer', ProjectTypeScope.GLOBAL, True),
        ('designer', ProjectTypeScope.PRIVATE, True),
        ('regular', ProjectTypeScope.GLOBAL, False),
        ('regular', ProjectTypeScope.PRIVATE, True),
    ])
    def test_create_design(self, user, scope, expected):
        user = create_user(is_designer=user == 'designer')
        res = api_client(user).post(reverse('projecttype-list'), data={'name': 'Test', 'scope': scope})
        assert (res.status_code == 201) == expected
        if expected:
            assert res.data['scope'] == scope
            pt = ProjectType.objects.get(id=res.data['id'])
            assert pt.scope == scope
            assert pt.linked_project is None
            assert pt.linked_user == (user if scope == 'private' else None)

    @pytest.mark.parametrize('user,scope,expected', [
        ('designer', ProjectTypeScope.GLOBAL, True),
        ('designer', ProjectTypeScope.PRIVATE, True),
        ('regular', ProjectTypeScope.GLOBAL, False),
        ('regular', ProjectTypeScope.PRIVATE, True),
    ])
    def test_import_design(self, user, scope, expected):
        pt_file = io.BytesIO(b''.join(export_project_types([create_project_type()])))
        user = create_user(is_designer=user == 'designer')
        res = api_client(user).post(reverse('projecttype-import'), data={'file': pt_file, 'scope': scope}, format='multipart')
        assert (res.status_code == 201) == expected
        if expected:
            assert res.data[0]['scope'] == scope
            pt = ProjectType.objects.get(id=res.data[0]['id'])
            assert pt.scope == scope
            assert pt.linked_project is None
            assert pt.linked_user == (user if scope == 'private' else None)

    @pytest.mark.parametrize('user,project_type,scope,expected', [
        ('designer', 'global', ProjectTypeScope.GLOBAL, True),
        ('designer', 'global', ProjectTypeScope.PRIVATE, True),
        ('designer', 'private', ProjectTypeScope.GLOBAL, True),
        ('designer', 'private', ProjectTypeScope.PRIVATE, True),

        ('regular', 'global', ProjectTypeScope.GLOBAL, False),
        ('regular', 'global', ProjectTypeScope.PRIVATE, True),
        ('regular', 'private', ProjectTypeScope.GLOBAL, False),
        ('regular', 'private', ProjectTypeScope.PRIVATE, True),
    ])
    def test_copy_design(self, user, project_type, scope, expected):
        user = create_user(is_designer=user == 'designer')
        project_type = create_project_type(linked_user=user if project_type == 'private' else None)
        res = api_client(user).post(reverse('projecttype-copy', kwargs={'pk': project_type.id}), data={'scope': scope})
        assert (res.status_code == 201) == expected
        if expected:
            assert res.data['scope'] == scope
            pt = ProjectType.objects.get(id=res.data['id'])
            assert pt.scope == scope
            assert pt.linked_project is None
            assert pt.linked_user == (user if scope == ProjectTypeScope.PRIVATE else None)
            assert pt.copy_of == project_type

