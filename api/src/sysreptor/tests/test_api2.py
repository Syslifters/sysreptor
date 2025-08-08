import io
from datetime import timedelta
from uuid import uuid4

import pytest
from django.urls import reverse
from django.utils import timezone

from sysreptor.pentests.cvss import CVSSLevel
from sysreptor.pentests.import_export import export_project_types
from sysreptor.pentests.models import (
    FindingTemplate,
    FindingTemplateTranslation,
    Language,
    ProjectType,
    ProjectTypeScope,
    ReviewStatus,
    SourceEnum,
)
from sysreptor.tests.mock import (
    api_client,
    create_project,
    create_project_type,
    create_template,
    create_user,
    create_usernotebookpage,
    mock_time,
    update,
)
from sysreptor.tests.utils import assertKeysEqual


@pytest.mark.django_db()
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
        # ProjectType.usage_count incremented
        self.project_type.refresh_from_db()
        assert self.project_type.usage_count == 1

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
        update(project.project_type, linked_project=project)

        # ProjectType not changed
        u = self.client.patch(reverse('pentestproject-detail', kwargs={'pk': project.id}), data={
            'project_type': project.project_type.id,
        }).json()
        assert u['project_type'] == str(project.project_type.id)

        # ProjectType changed
        p = self.client.patch(reverse('pentestproject-detail', kwargs={'pk': project.id}), data={
            'project_type': self.project_type.id,
        }).json()

        assert p['project_type'] not in [str(project.project_type.id), str(self.project_type.id)]
        pt = ProjectType.objects.get(id=p['project_type'])
        assert pt.source == SourceEnum.SNAPSHOT
        assert pt.linked_project == project

        # ProjectType.usage_count incremented
        self.project_type.refresh_from_db()
        assert self.project_type.usage_count == 1

    def test_change_imported_members(self):
        project = create_project(members=[self.user], imported_members=[{
            'id': uuid4(),
            'additional_field': 'test',
            'roles': [],
        }])
        res = self.client.patch(reverse('pentestproject-detail', kwargs={'pk': project.id}), data={
            'imported_members': [{'id': project.imported_members[0]['id'], 'roles': ['pentester']}],
        })
        assert res.status_code == 200
        project.refresh_from_db()
        assert project.imported_members[0]['roles'] == ['pentester']
        assert project.imported_members[0]['additional_field'] == 'test'

    def test_sort_findings(self):
        project = create_project(members=[self.user], findings_kwargs=[
            {'data': {'title': 'Finding 1'}, 'order': 5},
            {'data': {'title': 'Finding 2'}, 'order': 4},
            {'data': {'title': 'Finding 3'}, 'order': 1},
            {'data': {'title': 'Finding 4'}, 'order': 2},
            {'data': {'title': 'Finding 5'}, 'order': 3},
        ])
        def finding_by_title(title):
            return next(filter(lambda f: f.data['title'] == title, project.findings.all()))

        res = self.client.post(reverse('finding-sort', kwargs={'project_pk': project.id}), data=[
            {'id': finding_by_title('Finding 1').finding_id, 'order': 1},
            {'id': finding_by_title('Finding 2').finding_id, 'order': 2},
            {'id': finding_by_title('Finding 3').finding_id, 'order': 3},
        ])
        assert res.status_code == 200
        expected_order = [f'Finding {i + 1}' for i in range(5)]
        assert [project.findings.get(finding_id=f['id']).data['title'] for f in sorted(res.data, key=lambda f: f['order'])] == expected_order
        assert [f.data['title'] for f in project.findings.order_by('order')] == expected_order

    @pytest.mark.parametrize(('filters', 'results'), [
        # Member
        ({'member': 'user1'}, ['p1']),
        ({'not_member': 'user2'}, ['p1']),
        ({'member': 'invalid'}, []),
        # Tag
        ({'tag': 'tag1'}, ['p1']),
        ({'not_tag': 'tag2'}, ['p1']),
        # Language
        ({'language': Language.ENGLISH_US.value}, ['p1']),
        ({'not_language': Language.ENGLISH_US.value}, ['p2']),
        ({'language': 'invalid'}, []),
        # Created
        ({'timerange': f'|{(timezone.now() - timedelta(days=2)).date().isoformat()}'}, ['p1']),
        ({'timerange': f'null|{(timezone.now() - timedelta(days=2)).date().isoformat()}'}, ['p1']),
        ({'timerange': f'{(timezone.now() - timedelta(days=2)).date().isoformat()}|'}, ['p2']),
        ({'timerange': f'{(timezone.now() - timedelta(days=2)).date().isoformat()}|null'}, ['p2']),
        ({'timerange': f'{(timezone.now() - timedelta(days=30)).date().isoformat()}|{(timezone.now() - timedelta(days=2)).date().isoformat()}'}, ['p1']),
        ({'not_timerange': f'|{(timezone.now() - timedelta(days=2)).date().isoformat()}'}, ['p2']),
        ({'not_timerange': f'null|{(timezone.now() - timedelta(days=2)).date().isoformat()}'}, ['p2']),
        ({'not_timerange': f'{(timezone.now() - timedelta(days=2)).date().isoformat()}|'}, ['p1']),
        ({'not_timerange': f'{(timezone.now() - timedelta(days=2)).date().isoformat()}|null'}, ['p1']),
        ({'not_timerange': f'{(timezone.now() - timedelta(days=30)).date().isoformat()}|{(timezone.now() - timedelta(days=2)).date().isoformat()}'}, ['p2']),
        # Created: invalid formats
        ({'timerange': ''}, ['p1', 'p2']),
        ({'timerange': 'null|null'}, ['p1', 'p2']),
        ({'timerange': f'{timezone.now().date().isoformat()}|{(timezone.now()).date().isoformat()}|{timezone.now().date().isoformat()}'}, ['p1', 'p2']),
        ({'timerange': 'invalid'}, ['p1', 'p2']),
        ({'timerange': 'invalid|invalid'}, ['p1', 'p2']),
        # Combine filters
        ({'member': ['user1', 'user2']}, ['p1', 'p2']),  # Same filter: OR
        ({'member': 'user1', 'tag': 'tag:all'}, ['p1']),  # Different filters: AND
        ({'tag': 'tag:all', 'not_tag': 'tag2'}, ['p1']),  # Not filters: AND
    ])
    def test_filters(self, filters, results):
        with mock_time(before=timedelta(days=10)):
            create_project(name='p1', project_type=self.project_type, members=[self.user, create_user(username='user1')], tags=['tag1', 'tag:all'], language=Language.ENGLISH_US)
        create_project(name='p2', project_type=self.project_type, members=[self.user, create_user(username='user2')], tags=['tag2', 'tag:all'], language=Language.GERMAN_DE)

        res = self.client.get(reverse('pentestproject-list', query=filters))
        assert set(p['name'] for p in res.data['results']) == set(results)


@pytest.mark.django_db()
class TestProjectTypeApi:
    @pytest.mark.parametrize(('user', 'scope', 'expected'), [
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

    @pytest.mark.parametrize(('user', 'scope', 'expected'), [
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

    @pytest.mark.parametrize(('user', 'project_type', 'scope', 'expected'), [
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

    @pytest.mark.parametrize(('filters', 'results'), [
        # Status
        ({'status': ReviewStatus.FINISHED}, ['pt1']),
        ({'not_status': ReviewStatus.FINISHED}, ['pt2']),
        ({'status': 'invalid'}, []),
        # Tag
        ({'tag': 'tag1'}, ['pt1']),
        ({'not_tag': 'tag2'}, ['pt1']),
        ({'tag': 'tag:all'}, ['pt1', 'pt2']),
        ({'not_tag': 'tag:all'}, []),
        # Language
        ({'language': Language.ENGLISH_US.value}, ['pt1']),
        ({'not_language': Language.ENGLISH_US.value}, ['pt2']),
        ({'language': 'invalid'}, []),
        # Created (timerange)
        ({'timerange': f'{(timezone.now() - timedelta(days=30)).date().isoformat()}|{(timezone.now() - timedelta(days=2)).date().isoformat()}'}, ['pt1']),
        ({'not_timerange': f'{(timezone.now() - timedelta(days=30)).date().isoformat()}|{(timezone.now() - timedelta(days=2)).date().isoformat()}'}, ['pt2']),
    ])
    def test_filters(self, filters, results):
        with mock_time(before=timedelta(days=10)):
            create_project_type(name='pt1', status=ReviewStatus.FINISHED, tags=['tag1', 'tag:all'], language=Language.ENGLISH_US)
        create_project_type(name='pt2', status=ReviewStatus.IN_PROGRESS, tags=['tag2', 'tag:all'], language=Language.GERMAN_DE)

        res = api_client(create_user(is_designer=True)).get(reverse('projecttype-list'), data=filters)
        assert res.status_code == 200
        assert set(pt['name'] for pt in res.data['results']) == set(results)


@pytest.mark.django_db()
class TestTemplateApi:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user(is_template_editor=True)
        self.client = api_client(self.user)
        self.template = create_template(language=Language.ENGLISH_US, translations_kwargs=[{'language': Language.GERMAN_DE}])
        self.trans_en = self.template.main_translation
        self.trans_de = self.template.translations.get(language=Language.GERMAN_DE)

    @pytest.mark.parametrize(('translations', 'expected'), [
        ([], False),
        ([{'is_main': False}], False),
        ([{'is_main': True, 'language': Language.ENGLISH_US}, {'is_main': True, 'language': Language.GERMAN_DE}], False),
        ([{'is_main': True, 'language': Language.ENGLISH_US}, {'is_main': False, 'language': Language.ENGLISH_US}], False),
        ([{'is_main': True, 'language': Language.ENGLISH_US}, {'is_main': False, 'language': Language.GERMAN_DE}], True),
    ])
    def test_create(self, translations, expected):
        res = self.client.post(reverse('findingtemplate-list'), data={
            'tags': ['test'],
            'translations': [{'language': Language.ENGLISH_US, 'data': {'title': 'test'}} | t for t in translations],
        })
        assert (res.status_code == 201) is expected, res.data

    def test_copy_template(self):
        cp = self.client.post(reverse('findingtemplate-copy', kwargs={'pk': self.template.id})).json()
        assert cp['id'] != str(self.template.id)
        assert cp['copy_of'] == str(self.template.id)

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
        data['translations'][0]['language'] = Language.GERMAN_DE
        data['translations'][1]['language'] = Language.ENGLISH_US
        assert self.update_template(self.template, data).status_code == 200
        assert self.trans_en.language == Language.GERMAN_DE.value
        assert self.trans_de.language == Language.ENGLISH_US.value

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
        update(self.trans_en, data={'title': 'title main', 'description': 'description main'})
        assert self.client.patch(reverse('findingtemplatetranslation-detail', kwargs={'template_pk': self.template.id, 'pk': self.trans_de.id}), {
            'data': {
                'title': 'title translation',
                'description': 'description translation',
            },
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
            },
        })
        f2 = self.client.post(reverse('finding-fromtemplate', kwargs={'project_pk': project.id}), data={
            'template': self.template.id,
            'template_language': self.trans_de.language,
        })
        assert f2.status_code == 201
        assert f2.data['data']['title'] == 'title translation'
        assert f2.data['data']['description'] == 'description main'

        # Template.usage_count incremented
        self.template.refresh_from_db()
        assert self.template.usage_count == 2

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
            },
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

    def assert_search_result(self, params, expected_result):
        res = self.client.get(reverse('findingtemplate-list'), data=params)
        assert res.status_code == 200
        assert [t['id'] for t in res.data['results']] == [str(t.id) for t in expected_result]

    def test_template_search(self):
        search_term = 'tls crypt'
        t_title_tag_data_de = create_template(language=Language.GERMAN_DE, data={'title': 'Weak TLS', 'description': 'Weak crypto'}, tags=['crypto'])
        t_title_data_en_de = create_template(language=Language.ENGLISH_US, data={'title': 'Weak TLS', 'description': 'Weak crypto'},
                                             translations_kwargs=[{'language': Language.GERMAN_DE, 'data': {'title': 'Weak TLS', 'description': 'Weak crypto'}}])
        t_data_en = create_template(language=Language.ENGLISH_US, data={'title': 'Unrelated', 'description': 'Improve TLS encryption'})
        t_partial_term_match = create_template(language=Language.GERMAN_DE, data={'title': 'Unrelated', 'description': 'Improve TLS'})
        t_no_match = create_template(language=Language.GERMAN_DE, data={'title': 'Unrelated', 'description': 'Unrelated'})

        # Best match first ordered by search rank
        self.assert_search_result({'search': search_term}, [t_title_tag_data_de, t_title_data_en_de, t_data_en])
        # Templates of preferred language first, then other languages, ordered by search rank
        self.assert_search_result({'search': search_term, 'preferred_language': Language.ENGLISH_US}, [t_title_data_en_de, t_data_en, t_title_tag_data_de])
        # Only templates of language, ordered by search rank
        self.assert_search_result({'search': search_term, 'language': Language.ENGLISH_US}, [t_title_data_en_de, t_data_en])
        # All templates
        self.assert_search_result({}, [t_no_match, t_partial_term_match, t_data_en, t_title_data_en_de, t_title_tag_data_de, self.template])

    @pytest.mark.parametrize(('ordering', 'expected'), [
        ('-created', ['t3', 't2', 't1']),
        ('created', ['t1', 't2', 't3']),
        ('updated', ['t1', 't3', 't2']),
        ('-updated', ['t2', 't3', 't1']),
        ('risk', ['t2', 't1', 't3']),
        ('-risk', ['t3', 't1', 't2']),
    ])
    def test_template_sort(self, ordering, expected):
        self.template.delete()
        create_template(data={'title': 't1', 'severity': CVSSLevel.MEDIUM})
        t2 = create_template(data={'title': 't2', 'severity': CVSSLevel.INFO})
        create_template(data={'title': 't3', 'severity': CVSSLevel.HIGH})
        t2.save()  # Update to change updated field

        res = self.client.get(reverse('findingtemplate-list'), data={'ordering': ordering})
        assert [t['translations'][0]['data']['title'] for t in res.data['results']] == expected

    @pytest.mark.parametrize(('filters', 'results'), [
        # Status
        ({'status': ReviewStatus.FINISHED}, ['t1']),
        ({'not_status': ReviewStatus.FINISHED}, ['t2']),
        ({'status': 'invalid'}, []),
        # Risk level
        ({'risk_level': CVSSLevel.HIGH}, ['t1']),
        ({'not_risk_level': CVSSLevel.HIGH}, ['t2']),
        ({'risk_level': 'invalid'}, []),
        # Tag
        ({'tag': 'tag1'}, ['t1']),
        ({'not_tag': 'tag2'}, ['t1']),
        ({'tag': 'tag:all'}, ['t1', 't2']),
        ({'not_tag': 'tag:all'}, []),
        # Language
        ({'language': Language.ENGLISH_US.value}, ['t1']),
        ({'not_language': Language.ENGLISH_US.value}, ['t2']),
        ({'language': 'invalid'}, []),
        # Created (timerange)
        ({'timerange': f'{(timezone.now() - timedelta(days=30)).date().isoformat()}|{(timezone.now() - timedelta(days=2)).date().isoformat()}'}, ['t1']),
        ({'not_timerange': f'{(timezone.now() - timedelta(days=30)).date().isoformat()}|{(timezone.now() - timedelta(days=2)).date().isoformat()}'}, ['t2']),
        # Timerange: invalid formats
        ({'timerange': ''}, ['t1', 't2']),
        ({'timerange': 'null|null'}, ['t1', 't2']),
        ({'timerange': 'invalid'}, ['t1', 't2']),
        # Combine filters
        ({'status': ReviewStatus.FINISHED, 'tag': 'tag1'}, ['t1']),  # Different filters: AND
        ({'tag': 'tag:all', 'not_tag': 'tag2'}, ['t1']),  # Not filters: AND
    ])
    def test_filters(self, filters, results):
        # Delete existing template from setUp
        self.template.delete()

        with mock_time(before=timedelta(days=10)):
            create_template(
                data={'title': 't1', 'severity': CVSSLevel.HIGH},
                status=ReviewStatus.FINISHED,
                tags=['tag1', 'tag:all'],
                language=Language.ENGLISH_US,
            )
        create_template(
            data={'title': 't2', 'severity': CVSSLevel.INFO},
            status=ReviewStatus.IN_PROGRESS,
            tags=['tag2', 'tag:all'],
            language=Language.GERMAN_DE,
        )

        res = self.client.get(reverse('findingtemplate-list'), data=filters)
        assert res.status_code == 200
        assert set(t['translations'][0]['data']['title'] for t in res.data['results']) == set(results)


@pytest.mark.django_db()
class TestNotesApi:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user()
        self.client = api_client(self.user)

    def test_sort(self):
        note1 = create_usernotebookpage(user=self.user, parent=None, order=3)
        top_level = [
            note1,
            create_usernotebookpage(user=self.user, parent=None, order=1),
            create_usernotebookpage(user=self.user, parent=None, order=2),
        ]
        sub_level = [
            create_usernotebookpage(user=self.user, parent=note1, order=2),
            create_usernotebookpage(user=self.user, parent=note1, order=3),
            create_usernotebookpage(user=self.user, parent=note1, order=1),
        ]

        res = self.client.post(reverse('usernotebookpage-sort', kwargs={'pentestuser_pk': 'self'}), data=
            [{'id': n.note_id, 'parent': None, 'order': idx + 1} for idx, n in enumerate(top_level)] +
            [{'id': n.note_id, 'parent': n.parent.note_id, 'order': idx + 1} for idx, n in enumerate(sub_level)],
        )
        assert res.status_code == 200, res.data
        for idx, n in enumerate(top_level):
            n.refresh_from_db()
            assert n.parent is None
            assert n.order == idx + 1
            assert next(filter(lambda rn: rn['id'] == str(n.note_id), res.data))['order'] == n.order
        for idx, n in enumerate(sub_level):
            n.refresh_from_db()
            assert n.parent == note1
            assert n.order == idx + 1
            assert next(filter(lambda rn: rn['id'] == str(n.note_id), res.data))['order'] == n.order

    def test_sort_change_parent(self):
        note1 = create_usernotebookpage(user=self.user, parent=None, order=1)
        note2 = create_usernotebookpage(user=self.user, parent=None, order=2)
        note1_1 = create_usernotebookpage(user=self.user, parent=note2, order=1)
        note1_2 = create_usernotebookpage(user=self.user, parent=None, order=3)
        note2_1 = create_usernotebookpage(user=self.user, parent=note1, order=1)
        note3 = create_usernotebookpage(user=self.user, parent=note1, order=2)

        res = self.client.post(reverse('usernotebookpage-sort', kwargs={'pentestuser_pk': 'self'}), data=[
            {'id': note1.note_id, 'parent': None, 'order': 1},
            {'id': note1_1.note_id, 'parent': note1.note_id, 'order': 1},
            {'id': note1_2.note_id, 'parent': note1.note_id, 'order': 2},
            {'id': note2.note_id, 'parent': None, 'order': 2},
            {'id': note2_1.note_id, 'parent': note2.note_id, 'order': 1},
            {'id': note3.note_id, 'parent': None, 'order': 3},
        ])
        assert res.status_code == 200, res.data
        for n in [note1, note2, note3, note1_1, note1_2, note2_1]:
            n.refresh_from_db()
        assert note1.parent is None
        assert note2.parent is None
        assert note3.parent is None
        assert note1_1.parent == note1
        assert note1_2.parent == note1
        assert note2_1.parent == note2

    def test_delete_children(self):
        self.user.notes.all().delete()

        note1 = create_usernotebookpage(user=self.user, parent=None, order=1)
        note1_1 = create_usernotebookpage(user=self.user, parent=note1, order=1)
        create_usernotebookpage(user=self.user, parent=note1, order=2)
        create_usernotebookpage(user=self.user, parent=note1_1, order=1)
        note2 = create_usernotebookpage(user=self.user, parent=None, order=2)
        note2_1 = create_usernotebookpage(user=self.user, parent=note2, order=1)

        res = self.client.delete(reverse('usernotebookpage-detail', kwargs={'pentestuser_pk': 'self', 'id': note1.note_id}))
        assert res.status_code == 204, res.data
        assert set(n.id for n in self.user.notes.all()) == {note2.id, note2_1.id}

    def test_export_multiple(self):
        self.user.notes.all().delete()

        note1 = create_usernotebookpage(user=self.user, parent=None, order=1)
        note1_1 = create_usernotebookpage(user=self.user, parent=note1, order=1)
        _note1_2 = create_usernotebookpage(user=self.user, parent=note1, order=2)
        note2 = create_usernotebookpage(user=self.user, parent=None, order=2)

        res = self.client.post(reverse('usernotebookpage-export-all', kwargs={'pentestuser_pk': 'self'}), data={
            'notes': [note1_1.note_id, note2.note_id],
        })
        assert res.status_code == 200, res.data
        archive = b''.join(res.streaming_content)

        self.user.notes.all().delete()
        res2 = self.client.post(reverse('usernotebookpage-import', kwargs={'pentestuser_pk': 'self'}), data={
            'file': io.BytesIO(archive),
        }, format='multipart')
        assert len(res2.data) == 2

    def test_copy_note(self):
        note_id = self.user.notes.first().note_id
        cp = self.client.post(reverse('usernotebookpage-copy', kwargs={'pentestuser_pk': 'self', 'id': note_id})).json()
        assert cp['id'] != str(note_id)
