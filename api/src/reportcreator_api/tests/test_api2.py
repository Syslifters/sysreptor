import io
from uuid import uuid4
from django.urls import reverse
import pytest

from reportcreator_api.archive.import_export.import_export import export_project_types
from reportcreator_api.pentests.cvss import CVSSLevel
from reportcreator_api.pentests.models import ProjectType, ProjectTypeScope, SourceEnum, FindingTemplate, FindingTemplateTranslation, Language, ReviewStatus
from reportcreator_api.tests.mock import create_project, create_project_type, create_template, create_user, api_client
from reportcreator_api.tests.utils import assertKeysEqual


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


@pytest.mark.django_db
class TestTemplateApi:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user(is_template_editor=True)
        self.client = api_client(self.user)
        self.template = create_template(language=Language.ENGLISH, translations_kwargs=[{'language': Language.GERMAN}])
        self.trans_en = self.template.main_translation
        self.trans_de = self.template.translations.get(language=Language.GERMAN)

    @pytest.mark.parametrize(['translations', 'expected'], [
        ([], False),
        ([{'is_main': False}], False),
        ([{'is_main': True, 'language': Language.ENGLISH}, {'is_main': True, 'language': Language.GERMAN}], False),
        ([{'is_main': True, 'language': Language.ENGLISH}, {'is_main': False, 'language': Language.ENGLISH}], False),
        ([{'is_main': True, 'language': Language.ENGLISH}, {'is_main': False, 'language': Language.GERMAN}], True),
    ])
    def test_create(self, translations, expected):
        res = self.client.post(reverse('findingtemplate-list'), data={
            'tags': ['test'],
            'translations': [{'language': Language.ENGLISH, 'data': {'title': 'test'}} | t for t in translations],
        })
        assert (res.status_code == 201) is expected, res.data

    def update_template(self, template, data):
        res = self.client.put(reverse('findingtemplate-detail', kwargs={'pk': self.template.id}), data)
        self.template.refresh_from_db()
        try:
            self.trans_en.refresh_from_db()
        except FindingTemplateTranslation.DoesNotExist:
            self.trans_en = None
        try:
            self.trans_de.refresh_from_db()
        except FindingTemplateTranslation.DoesNotExist:
            self.trans_de = None
        return res

    def test_update_swap_languages(self):
        data = self.client.get(reverse('findingtemplate-detail', kwargs={'pk': self.template.id})).data
        data['translations'][0]['language'] = Language.GERMAN
        data['translations'][1]['language'] = Language.ENGLISH
        assert self.update_template(self.template, data).status_code == 200
        assert self.trans_en.language == Language.GERMAN.value
        assert self.trans_de.language == Language.ENGLISH.value
    
    def test_update_change_main(self):
        data = self.client.get(reverse('findingtemplate-detail', kwargs={'pk': self.template.id})).data
        data['translations'][0]['is_main'] = False
        data['translations'][1]['is_main'] = True
        assert self.update_template(self.template, data).status_code == 200
        assert not self.trans_en.is_main
        assert self.trans_de.is_main
        assert self.template.main_translation == self.trans_de
    
    def test_update_add_delete_translations(self):
        data = self.client.get(reverse('findingtemplate-detail', kwargs={'pk': self.template.id})).data
        data['translations'][1] = {
            'language': Language.SPANISH,
            'status': ReviewStatus.IN_PROGRESS,
            'data': {
                'title': 'Spanish translation',
                'cvss': 'CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:L/A:N/CR:H',
            },
        }
        assert self.update_template(self.template, data).status_code == 200
        assert self.template.translations.all().count() == 2
        trans_es = self.template.translations.get(language=Language.SPANISH)
        assertKeysEqual(trans_es, data['translations'][1], ['language', 'status', 'data'])
        assert trans_es.risk_score == 10.0
        assert trans_es.risk_level == CVSSLevel.CRITICAL.value

    def test_update_delete_main(self):
        data = self.client.get(reverse('findingtemplate-detail', kwargs={'pk': self.template.id})).data
        del data['translations'][0]
        assert self.update_template(self.template, data).status_code == 400

        data['translations'][0]['is_main'] = True
        assert self.update_template(self.template, data).status_code == 200
        assert self.template.translations.all().count() == 1
        assert self.trans_de.is_main
        assert self.template.main_translation == self.trans_de

    def test_update_multiple_translations(self):
        data = self.client.get(reverse('findingtemplate-detail', kwargs={'pk': self.template.id})).data
        data['translations'][0]['data'] = {
            'title': 'Updated EN',
            'cvss': 'CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:L/A:N/CR:H',
        }
        data['translations'][1]['data'] = {
            'title': 'Updated DE',
        }
        assert self.update_template(self.template, data).status_code == 200
        assert self.trans_en.data == data['translations'][0]['data'] | {'unknown_field': 'test'}
        assert self.trans_de.data == data['translations'][1]['data']
        # Risk score inherited from main translation if not defined
        assert self.trans_en.risk_score == self.trans_de.risk_score == 10.0
        assert self.trans_en.risk_level == self.trans_de.risk_level == CVSSLevel.CRITICAL.value

    def test_delete_main_translation(self):
        assert self.client.delete(reverse('findingtemplatetranslation-detail', kwargs={'template_pk': self.template.id, 'pk': self.trans_en.id})).status_code == 400

    def test_create_finding_from_template(self):
        project = create_project(members=[self.user], images_kwargs=[])
        # Override field from main
        self.trans_en.update_data({'title': 'title main', 'description': 'description main'})
        self.trans_en.save()
        assert self.client.patch(reverse('findingtemplatetranslation-detail', kwargs={'template_pk': self.template.id, 'pk': self.trans_de.id}), {
            'data': {
                'title': 'title translation',
                'description': 'description translation',
            }
        }).status_code == 200
        f1 = self.client.post(reverse('finding-fromtemplate', kwargs={'project_pk': project.id}), data={
            'template': self.template.id,
            'template_language': self.trans_de.language,
        })
        assert f1.status_code == 201
        assert f1.data['data']['title'] == 'title translation'
        assert f1.data['data']['description'] == 'description translation'

        # Reset field to main
        self.client.patch(reverse('findingtemplatetranslation-detail', kwargs={'template_pk': self.template.id, 'pk': self.trans_de.id}), {
            'data': {
                'title': 'title translation',
            }
        })
        f2 = self.client.post(reverse('finding-fromtemplate', kwargs={'project_pk': project.id}), data={
            'template': self.template.id,
            'template_language': self.trans_de.language,
        })
        assert f2.status_code == 201
        assert f2.data['data']['title'] == 'title translation'
        assert f2.data['data']['description'] == 'description main'

    def test_create_finding_from_template_images(self):
        template = create_template(data={'description': '![image](/images/name/image.png)'}, images_kwargs=[{'name': 'image.png'}])
        project = create_project(members=[self.user], findings_kwargs=[], images_kwargs=[])

        # Template image copied to project
        f1 = self.client.post(reverse('finding-fromtemplate', kwargs={'project_pk': project.id}), data={'template': template.id})
        assert f1.status_code == 201
        assert project.images.count() == 1
        img1 = project.images.filter_name('image.png').get()
        assert img1.file.read() == template.images.first().file.read()
        assert f1.data['data']['description'] == '![image](/images/name/image.png)'

        # Template image name already exists in project. Image is renamed and copied
        f2 = self.client.post(reverse('finding-fromtemplate', kwargs={'project_pk': project.id}), data={'template': template.id})
        assert f2.status_code == 201
        assert project.images.count() == 2
        img2 = project.images.order_by('-created').first()
        assert img2.name != 'image.png'
        assert img2.file.read() == template.images.first().file.read()
        assert f2.data['data']['description'] == f'![image](/images/name/{img2.name})'

    def test_create_template_from_finding(self):
        project = create_project(members=[self.user], findings_kwargs=[{
            'data': {
                'title': 'finding title',
                'description': '![image](/images/name/image.png)',
            }
        }], images_kwargs=[{'name': 'image.png'}, {'name': 'image_unreferenced.png'}])
        finding = project.findings.first()

        res = self.client.post(reverse('findingtemplate-fromfinding'), data={
            'project': project.id,
            'translations': [{
                'is_main': True,
                'language': project.language,
                'data': finding.data,
            }],
        })
        assert res.status_code == 201, res.data
        template = FindingTemplate.objects.get(id=res.data['id'])
        assert template.main_translation.data == finding.data
        assert template.images.count() == 1
        img = template.images.first()
        assert img.name == 'image.png'
        assert img.file.read() == project.images.filter_name(img.name).get().file.read()

