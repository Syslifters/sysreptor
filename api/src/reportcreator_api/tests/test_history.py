import enum
from datetime import timedelta

import pytest
from asgiref.sync import async_to_sync
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from reportcreator_api.archive.import_export.import_export import (
    export_project_types,
    export_projects,
    export_templates,
    import_project_types,
    import_projects,
    import_templates,
)
from reportcreator_api.pentests.models import (
    FindingTemplate,
    FindingTemplateTranslation,
    Language,
    ProjectType,
    ReviewStatus,
    UploadedTemplateImage,
)
from reportcreator_api.pentests.models.files import UploadedAsset, UploadedImage
from reportcreator_api.pentests.models.notes import ProjectNotebookPage
from reportcreator_api.pentests.models.project import (
    PentestFinding,
    PentestProject,
    ProjectMemberInfo,
    ProjectMemberRole,
    ReportSection,
)
from reportcreator_api.pentests.tasks import cleanup_history
from reportcreator_api.tasks.models import PeriodicTask
from reportcreator_api.tests.mock import (
    api_client,
    create_finding,
    create_project,
    create_project_type,
    create_projectnotebookpage,
    create_template,
    create_template_translation,
    create_user,
    mock_time,
)
from reportcreator_api.tests.test_import_export import archive_to_file
from reportcreator_api.utils.utils import copy_keys, omit_keys


def has_changes(a, b):
    tracked_fields = a.tracked_fields if hasattr(a, 'tracked_fields') else a.history.model.tracked_fields if hasattr(a, 'history') else b.tracked_fields
    for f in tracked_fields:
        av = getattr(a, f.attname)
        bv = getattr(b, f.attname)
        if av != bv or \
           ((isinstance(av, enum.Enum) or isinstance(bv, enum.Enum)) and str(av) != str(bv)):
            return True
    return False


def assert_history(obj, history_count=None, history_type=None, history_date=None, history_change_reason=None, history_user=None, history_title=None):
    try:
        obj.refresh_from_db()
    except ObjectDoesNotExist:
        pass

    if history_count is not None:
        assert obj.history.all().count() == history_count

    h = obj.history.all()[0]
    if history_type:
        assert h.history_type == history_type
    if history_date:
        assert h.history_date == history_date
    if history_change_reason:
        assert h.history_change_reason == history_change_reason
    if history_user:
        assert h.history_user == history_user
    if history_title:
        assert h.history_title == history_title
    assert not has_changes(obj, h)


@pytest.mark.django_db
class TestTemplateHistory:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user(is_template_editor=True)
        self.client = api_client(self.user)

    def assert_template_history_create(self, template, **kwargs):
        for o in [template] + list(template.translations.all()) + list(template.images.all()):
            assert_history(o,
                           history_count=1,
                           history_type='+',
                           history_date=template.history.all()[0].history_date,
                           history_title=o.get_language_display() if isinstance(o, FindingTemplateTranslation) else None,
                           **kwargs)

    def test_create_template_signal(self):
        t = FindingTemplate.objects.create(tags=['test'])
        assert_history(t, history_count=1, history_type='+')
        tr = FindingTemplateTranslation.objects.create(template=t, language=Language.FRENCH_FR, title='test')
        assert_history(tr, history_count=1, history_type='+')

    def test_copy(self):
        t = create_template().copy()
        self.assert_template_history_create(t, history_change_reason='Duplicated')

    @pytest.mark.parametrize(['changes', 'change_reason'], [
        ({'status': ReviewStatus.FINISHED}, 'Status changed to Finished'),
        ({'language': Language.FRENCH_FR}, 'Language changed to French (fr-FR)'),
        ({'data': {'title': 'changed title'}}, None),
    ])
    def test_update_translation(self, changes, change_reason):
        t = create_template()
        tr = t.main_translation
        tr_initial = FindingTemplateTranslation.objects.get(id=tr.id)

        def reset_state():
            tr_initial.save()
            tr.history.all().delete()

        def assert_history_update(api=False):
            tr.refresh_from_db()
            assert_history(tr, history_count=1, history_type='~', history_change_reason=change_reason, **({'history_user': self.user} if api else {}))

        # Signal
        reset_state()
        for k, v in changes.items():
            if k == 'data':
                tr.update_data(v)
            else:
                setattr(tr, k, v)
        tr.save()
        assert_history_update(api=False)

        # API translation detail
        reset_state()
        self.client.patch(reverse('findingtemplatetranslation-detail', kwargs={'template_pk': t.id, 'pk': tr.id}), data=changes)
        assert_history_update(api=True)

        # API template sublist
        reset_state()
        data = self.client.get(reverse('findingtemplate-detail', kwargs={'pk': t.id})).data
        data['translations'][0].update(changes)
        self.client.patch(reverse('findingtemplate-detail', kwargs={'pk': t.id}), data=data)
        assert_history_update(api=True)

    def test_update_unchanged_no_history(self):
        tr = create_template().main_translation
        tr.history.all().delete()
        tr.save()
        assert tr.history.all().count() == 0

    def test_delete_translation_signal(self):
        tr = create_template().main_translation
        tr_id = tr.id
        tr.delete()
        tr.id = tr_id
        assert_history(tr, history_count=2, history_type='-')

    def test_delete_template(self):
        t = create_template()
        tid = t.id
        t.delete()
        assert FindingTemplate.history.filter(id=tid).count() == 0
        assert FindingTemplateTranslation.history.filter(template_id=tid).count() == 0
        assert UploadedTemplateImage.history.filter(linked_object_id=tid).count() == 0

    def test_create_template_api(self):
        res = self.client.post(reverse('findingtemplate-list'), data={
            'tags': ['test'],
            'translations': [
                {'is_main': True, 'language': Language.ENGLISH_US, 'data': {'title': 'test'}},
                {'is_main': False, 'language': Language.GERMAN_DE, 'data': {'title': 'test'}},
            ],
        })
        assert res.status_code == 201
        self.assert_template_history_create(FindingTemplate.objects.get(id=res.data['id']))

    def test_create_from_finding_api(self):
        project = create_project(members=[self.user], findings_kwargs=[{
            'data': {
                'title': 'finding title',
                'description': '![image](/images/name/image.png)',
            },
        }], images_kwargs=[{'name': 'image.png'}, {'name': 'image_unreferenced.png'}])
        finding = project.findings.first()
        data = self.client.post(reverse('findingtemplate-fromfinding'), data={
            'project': project.id,
            'translations': [
                {'is_main': True, 'language': project.language, 'data': finding.data},
            ],
        }).data
        self.assert_template_history_create(FindingTemplate.objects.get(id=data['id']))

    def test_update_template_api(self):
        t = create_template(tags=['test'], data={'title': 'test'}, translations_kwargs=[{'language': Language.GERMAN_DE, 'data': {'title': 'test'}}])
        tr1 = t.main_translation
        tr2 = t.translations.get(language=Language.GERMAN_DE)

        # Update without changes: no history
        res = self.client.patch(reverse('findingtemplate-detail', kwargs={'pk': t.id}), data=self.client.get(reverse('findingtemplate-detail', kwargs={'pk': t.id})).data)
        assert res.status_code == 200
        self.assert_template_history_create(t)

        # Create translation
        data = self.client.get(reverse('findingtemplate-detail', kwargs={'pk': t.id})).data
        data['translations'].append({'language': Language.SPANISH})
        res = self.client.patch(reverse('findingtemplate-detail', kwargs={'pk': t.id}), data=data)
        assert res.status_code == 200
        tr3 = t.translations.get(language=Language.SPANISH)
        assert_history(tr3, history_count=1, history_type='+', history_user=self.user)

        # Delete translation
        data['translations'] = [tr for tr in data['translations'] if tr['language'] != Language.SPANISH]
        res = self.client.patch(reverse('findingtemplate-detail', kwargs={'pk': t.id}), data=data)
        assert res.status_code == 200
        assert_history(tr3, history_count=2, history_type='-', history_user=self.user)

        # Update template tags
        data['tags'].append('new')
        res = self.client.patch(reverse('findingtemplate-detail', kwargs={'pk': t.id}), data=data)
        assert res.status_code == 200
        assert_history(t, history_count=2, history_type='~', history_change_reason=None, history_user=self.user)

        # Change main_translation
        data['translations'][0]['is_main'] = False
        data['translations'][1]['is_main'] = True
        res = self.client.patch(reverse('findingtemplate-detail', kwargs={'pk': t.id}), data=data)
        assert res.status_code == 200
        assert_history(t, history_count=3, history_type='~', history_change_reason='Main translation changed to German (de-DE)', history_user=self.user)

        assert_history(tr1, history_count=1, history_type='+')
        assert_history(tr2, history_count=1, history_type='+')

    def format_template(self, template_data):
        out = omit_keys(template_data, ['updated', 'lock_info', 'usage_count'])
        out['translations'] = sorted([omit_keys(tr, ['updated']) for tr in out.get('translations', [])], key=lambda tr: tr['id'])
        return out

    def test_history_api(self):
        t = create_template(language=Language.ENGLISH_US, tags=['tag1'], data={'title': 'title 1'}, translations_kwargs=[], images_kwargs=[])
        tr1 = t.main_translation
        tr1_id = tr1.id
        history = []

        def add_history_test():
            history.append({
                'history_date': timezone.now(),
                'template': self.client.get(reverse('findingtemplate-detail', kwargs={'pk': t.id})).data,
                'images': {i.name: i.file.read() for i in t.images.all()},
            })

        # Initial template
        add_history_test()
        # Upload image
        ti1 = UploadedTemplateImage.objects.create(linked_object=t, name='file-new.png', file=SimpleUploadedFile(name='file-new.png', content=b'file-new'))
        add_history_test()
        # Add translation
        tr2 = create_template_translation(template=t, language=Language.GERMAN_DE, data={'title': 'title 2'})
        add_history_test()
        # Update template and translation
        t.tags = ['tag2']
        t.save()
        tr1.update_data({'title': 'title 1 updated'})
        tr1.save()
        add_history_test()
        # Replace image
        ti1.delete()
        UploadedTemplateImage.objects.create(linked_object=t, name='file-new2.png', file=SimpleUploadedFile(name='file-new2.png', content=b'file-new2'))
        add_history_test()
        # Change main translation
        t.main_translation = tr2
        t.save()
        tr1.delete()
        add_history_test()

        assert self.client.get(reverse('findingtemplatetranslation-history-timeline', kwargs={'template_pk': t.id, 'pk': tr1_id})).status_code == 200
        assert self.client.get(reverse('findingtemplatetranslation-history-timeline', kwargs={'template_pk': t.id, 'pk': tr2.id})).status_code == 200

        # Test history entries
        for h in history:
            res_t = self.client.get(reverse('findingtemplatehistory-detail', kwargs={'template_pk': t.id, 'history_date': h['history_date'].isoformat()}))
            assert res_t.status_code == 200
            assert self.format_template(res_t.data) == self.format_template(h['template'])
            for name, content in h['images'].items():
                res_i = self.client.get(reverse('findingtemplatehistory-image-by-name', kwargs={'template_pk': t.id, 'history_date': h['history_date'].isoformat(), 'filename': name}))
                assert res_i.status_code == 200
                assert b''.join(iter(res_i)) == content

    def test_history_import(self):
        t = import_templates(archive_to_file(export_templates([create_template()])))[0]
        self.assert_template_history_create(t, history_change_reason='Imported')

    def test_history_api_show_deleted(self):
        t = create_template(translations_kwargs=[{'language': Language.GERMAN_DE, 'data': {'title': 'title'}}])
        tr = t.translations.get(language=Language.GERMAN_DE)
        tr_id = tr.id
        ref_before_delete = self.client.get(reverse('findingtemplate-detail', kwargs={'pk': t.id})).data
        tr.history.all().delete()
        tr.delete()

        # Historic record at delete time
        timeline = self.client.get(reverse('findingtemplatetranslation-history-timeline', kwargs={'template_pk': t.id, 'pk': tr_id})).data['results']
        res_deleted = self.client.get(reverse('findingtemplatehistory-detail', kwargs={'template_pk': t.id, 'history_date': timeline[0]['history_date']}))
        assert res_deleted.status_code == 200
        assert self.format_template(res_deleted.data) == self.format_template(ref_before_delete)

        # Historic record after delete
        res_after_delete = self.client.get(reverse('findingtemplatehistory-detail', kwargs={'template_pk': t.id, 'history_date': timezone.now().isoformat()}))
        assert self.format_template(res_after_delete.data) != self.format_template(res_after_delete)
        assert len(res_after_delete.data['translations']) == 1


@pytest.mark.django_db
class TestProjectTypeHistory:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user(is_designer=True)
        self.client = api_client(self.user)

    def assert_history_create(self, pt, **kwargs):
        for o in [pt] + list(pt.assets.all()):
            assert_history(o,
                           history_count=1,
                           history_type='+',
                           history_date=pt.history.all()[0].history_date,
                           history_title=o.name,
                           **kwargs)

    def test_copy(self):
        pt = create_project_type().copy()
        self.assert_history_create(pt, history_change_reason='Duplicated')

    def test_import(self):
        pt = import_project_types(archive_to_file(export_project_types([create_project_type()])))[0]
        self.assert_history_create(pt, history_change_reason='Imported')

    def test_create_api(self):
        res = self.client.post(reverse('projecttype-list'), data={
            'name': 'test',
            'scope': 'global',
        })
        self.assert_history_create(ProjectType.objects.get(id=res.data['id']))

    def test_delete(self):
        pt = create_project_type()
        pt_id = pt.id
        pt.delete()
        ProjectType.history.filter(id=pt_id).count() == 0
        UploadedAsset.history.filter(linked_object_id=pt_id).count() == 0

    def test_history_api(self):
        pt = create_project_type()
        history = []

        def add_history_test():
            history.append({
                'history_date': timezone.now(),
                'instance': self.client.get(reverse('projecttype-detail', kwargs={'pk': pt.id})).data,
                'assets': {a.name: a.file.read() for a in pt.assets.all()},
            })

        # Initial
        add_history_test()
        # Upload asset
        a1 = UploadedAsset.objects.create(linked_object=pt, name='file-new.png', file=SimpleUploadedFile(name='file-new.png', content=b'file-new'))
        add_history_test()
        # Update fields
        pt.finding_fields = omit_keys(pt.finding_fields, ['cvss'])
        pt.save()
        add_history_test()
        # Delete asset
        a1.delete()
        add_history_test()
        # Update HTML and CSS
        pt.report_template = '<h1>{{ report.title}}</h1>'
        pt.report_styles = 'h1 { color: red; }'
        pt.save()
        add_history_test()

        assert self.client.get(reverse('projecttype-history-timeline', kwargs={'pk': pt.id})).status_code == 200

        # Test history entries
        for h in history:
            res_pt = self.client.get(reverse('projecttypehistory-detail', kwargs={'projecttype_pk': pt.id, 'history_date': h['history_date'].isoformat()}))
            assert res_pt.status_code == 200
            assert omit_keys(res_pt.data, ['updated', 'lock_info']) == omit_keys(h['instance'], ['updated', 'lock_info'])
            for name, content in h['assets'].items():
                res_i = self.client.get(reverse('projecttypehistory-asset-by-name', kwargs={'projecttype_pk': pt.id, 'history_date': h['history_date'].isoformat(), 'filename': name}))
                assert res_i.status_code == 200
                assert b''.join(iter(res_i)) == content


@pytest.mark.django_db
class TestProjectHistory:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user()
        self.client = api_client(self.user)

    def assert_history_create(self, project, **kwargs):
        objs = [project] + \
            list(project.sections.all()) + list(project.findings.all()) + list(project.notes.all()) + \
            list(project.images.all()) + list(project.files.all())
        for o in objs:
            assert_history(o,
                           history_count=1,
                           history_type='+',
                           history_date=project.history.all()[0].history_date,
                           history_title=o.section_label if isinstance(o, ReportSection) else
                                         o.data['title'] if isinstance(o, PentestFinding) else
                                         o.title if isinstance(o, ProjectNotebookPage) else
                                         o.name,
                           **kwargs)
        for o in list(project.members.all()):
            assert_history(o, history_count=1, history_type='+', history_date=project.history.all()[0].history_date, history_title=o.user.username)

    def test_copy(self):
        p = create_project(members=[self.user]).copy()
        self.assert_history_create(p, history_change_reason=f'Duplicated from project "{p.name}"')

    def test_import(self):
        p = import_projects(archive_to_file(export_projects([create_project(members=[self.user])])))[0]
        self.assert_history_create(p, history_change_reason='Imported')

    def test_create_api(self):
        res = self.client.post(reverse('pentestproject-list'), data={
            'name': 'test',
            'project_type': create_project_type().id,
        })
        self.assert_history_create(PentestProject.objects.get(id=res.data['id']))

    def test_delete(self):
        p = create_project(members=[self.user])
        pid = p.id
        p.delete()
        PentestProject.history.filter(id=pid).count() == 0
        PentestFinding.history.filter(project_id=pid).count() == 0
        ReportSection.history.filter(project_id=pid).count() == 0
        ProjectNotebookPage.history.filter(project_id=pid).count() == 0
        ProjectMemberInfo.history.filter(project_id=pid).count() == 0
        UploadedImage.history.filter(linked_object_id=pid).count() == 0
        UploadedAsset.history.filter(linked_object_id=pid).count() == 0

    def test_change_project_type(self):
        p = create_project(members=[self.user])
        sections_prev = list(p.sections.all())

        p.project_type = create_project_type(
            finding_fields=copy_keys(p.project_type.finding_fields, ['title', 'cvss']) | {'field_new': {'type': 'string'}},
            report_fields=copy_keys(p.project_type.finding_fields, ['title']),
            report_sections=[{'id': 'new', 'label': 'New', 'fields': ['title']}],
        )
        p.save()

        assert_history(p, history_count=2, history_type='~', history_change_reason='Design changed')
        assert_history(p.sections.get(section_id='new'), history_count=1, history_type='+', history_change_reason='Design changed')
        for s in sections_prev:
            assert_history(s, history_count=2, history_type='-', history_change_reason='Design changed')
        for f in p.findings.all():
            assert_history(f, history_count=2, history_type='~', history_change_reason='Design changed')

    def test_update_project_type_fields(self):
        p = create_project(members=[self.user])
        sections_prev = list(p.sections.all())
        p.project_type.finding_fields = copy_keys(p.project_type.finding_fields, ['title', 'cvss']) | {'field_new': {'type': 'string'}}
        p.project_type.report_fields = copy_keys(p.project_type.report_fields, ['title'])
        p.project_type.report_sections = [{'id': 'new', 'label': 'New', 'fields': ['title']}]
        p.project_type.save()

        assert_history(p, history_count=2, history_type='~', history_change_reason='Field definition changed')
        assert_history(p.sections.get(section_id='new'), history_count=1, history_type='+', history_change_reason='Field definition changed')
        for s in sections_prev:
            assert_history(s, history_count=2, history_type='-', history_change_reason='Field definition changed')
        for f in p.findings.all():
            assert_history(f, history_count=2, history_type='~', history_change_reason='Field definition changed')

    def test_history_api(self):
        p = create_project(members=[self.user])

        history = []
        def add_history_test():
            p.refresh_from_db()
            history.append({
                'history_date': timezone.now(),
                'project': self.client.get(reverse('pentestproject-detail', kwargs={'pk': p.id})).data,
                'project_type': self.client.get(reverse('projecttype-detail', kwargs={'pk': p.project_type.id})).data,
                'findings': [self.client.get(reverse('finding-detail', kwargs={'project_pk': p.id, 'id': f.finding_id})).data for f in p.findings.all()],
                'sections': [self.client.get(reverse('section-detail', kwargs={'project_pk': p.id, 'id': s.section_id})).data for s in p.sections.all()],
                'notes': [self.client.get(reverse('projectnotebookpage-detail', kwargs={'project_pk': p.id, 'id': n.note_id})).data for n in p.notes.all()],
                'images': {i.name: i.file.read() for i in p.images.all()},
                'files': {f.name: f.file.read() for f in p.images.all()},
            })

        # Initial
        add_history_test()

        # Create finding
        f = create_finding(project=p)
        add_history_test()
        # Update finding
        f.update_data({'title': 'new title'})
        f.save()
        add_history_test()
        # Delete finding
        f.delete()
        add_history_test()

        # Update section
        s = p.sections.get(section_id='executive_summary')
        s.update_data({'executive_summary': 'new content'})
        s.save()
        add_history_test()

        # Create note
        n = create_projectnotebookpage(project=p, title='title', text='text')
        add_history_test()
        # Update note
        n.title = 'new title'
        n.assignee = self.user
        n.save()
        add_history_test()
        # Delete note
        n.delete()
        add_history_test()

        # Add member
        u2 = create_user()
        m = ProjectMemberInfo.objects.create(project=p, user=u2, roles=['pentester'])
        add_history_test()
        # Update role
        m.roles = ['pentester', 'reviewer']
        m.save()
        add_history_test()
        # Remove member
        m.delete()
        add_history_test()

        # Change project_type
        p.project_type = create_project_type(
            finding_fields=copy_keys(p.project_type.finding_fields, ['title', 'cvss']) | {'field_new': {'type': 'string'}},
            report_fields=copy_keys(p.project_type.finding_fields, ['title']),
            report_sections=[{'id': 'new', 'label': 'New', 'fields': ['title']}],
        )
        p.save()
        add_history_test()

        # Update project_type fields
        p.project_type.finding_fields |= {'field_new2': {'type': 'string', 'default': 'test'}}
        p.project_type.report_fields |= {'field_new': {'type': 'string', 'default': 'test'}}
        p.save()
        add_history_test()

        assert self.client.get(reverse('pentestproject-history-timeline', kwargs={'pk': p.id})).status_code == 200
        assert self.client.get(reverse('section-history-timeline', kwargs={'project_pk': p.id, 'id': s.section_id})).status_code == 200
        assert self.client.get(reverse('finding-history-timeline', kwargs={'project_pk': p.id, 'id': f.finding_id})).status_code == 200
        assert self.client.get(reverse('projectnotebookpage-history-timeline', kwargs={'project_pk': p.id, 'id': n.note_id})).status_code == 200

        for h in history:
            url_kwargs = {'project_pk': p.id, 'history_date': h['history_date'].isoformat()}
            res_p = self.client.get(reverse('pentestprojecthistory-detail', kwargs=url_kwargs))
            assert res_p.status_code == 200
            assert omit_keys(res_p.data, ['updated', 'members', 'findings', 'sections']) == omit_keys(h['project'], ['updated', 'members', 'findings', 'sections'])
            assert {m['id']: m for m in res_p.data['members']} == {m['id']: m for m in h['project']['members']}
            assert {s['id']: omit_keys(s, ['updated', 'lock_info']) for s in res_p.data['sections']} == {s['id']: omit_keys(s, ['updated', 'lock_info']) for s in h['project']['sections']}
            assert {f['id']: omit_keys(f, ['updated', 'lock_info']) for f in res_p.data['findings']} == {f['id']: omit_keys(f, ['updated', 'lock_info']) for f in h['project']['findings']}

            res_pt = self.client.get(reverse('projecttypehistory-detail', kwargs={'projecttype_pk': h['project_type']['id'], 'history_date': h['history_date']}))
            assert omit_keys(res_pt.data, ['updated', 'lock_info']) == omit_keys(h['project_type'], ['updated', 'lock_info'])

            for fh in h['findings']:
                res_f = self.client.get(reverse('pentestprojecthistory-finding', kwargs=url_kwargs | {'id': fh['id']}))
                assert omit_keys(res_f.data, ['updated', 'lock_info']) == omit_keys(fh, ['updated', 'lock_info'])
            for sh in h['sections']:
                res_s = self.client.get(reverse('pentestprojecthistory-section', kwargs=url_kwargs | {'id': sh['id']}))
                assert omit_keys(res_s.data, ['updated', 'lock_info']) == omit_keys(sh, ['updated', 'lock_info'])
            for nh in h['notes']:
                res_n = self.client.get(reverse('pentestprojecthistory-note', kwargs=url_kwargs | {'id': nh['id']}))
                assert omit_keys(res_n.data, ['updated', 'lock_info']) == omit_keys(nh, ['updated', 'lock_info'])
            for name, content in h['images'].items():
                res_i = self.client.get(reverse('pentestprojecthistory-image-by-name', kwargs=url_kwargs | {'filename': name}))
                assert b''.join(iter(res_i)) == content
            for name, content in h['files'].items():
                res_i = self.client.get(reverse('pentestprojecthistory-image-by-name', kwargs=url_kwargs | {'filename': name}))
                assert b''.join(iter(res_i)) == content

    def test_history_referenceds_deleted_user(self):
        u = create_user()
        p = create_project(members=[self.user, u], findings_kwargs=[{'assignee': u}], notes_kwargs=[{'assignee': u}])
        f = p.findings.first()
        n = p.notes.first()
        s = p.sections.first()
        api_client(u).patch(reverse('section-detail', kwargs={'project_pk': p.id, 'id': s.section_id}), data={'assignee': {'id': u.id}})
        s.assignee = u
        s.save()

        history_date = timezone.now()
        p.members.get(user=u).delete()
        u.delete()

        assert self.client.get(reverse('pentestproject-history-timeline', kwargs={'pk': p.id})).status_code == 200
        assert self.client.get(reverse('section-history-timeline', kwargs={'project_pk': p.id, 'id': s.section_id})).status_code == 200
        assert self.client.get(reverse('finding-history-timeline', kwargs={'project_pk': p.id, 'id': f.finding_id})).status_code == 200
        assert self.client.get(reverse('projectnotebookpage-history-timeline', kwargs={'project_pk': p.id, 'id': n.note_id})).status_code == 200

        url_kwargs = {'project_pk': p.id, 'history_date': history_date.isoformat()}
        res_p = self.client.get(reverse('pentestprojecthistory-detail', kwargs=url_kwargs))
        assert res_p.status_code == 200
        assert len(res_p.data['members']) == 1  # Deleted user not included in members

        # Deleted assignee set null
        res_s = self.client.get(reverse('pentestprojecthistory-section', kwargs=url_kwargs | {'id': s.section_id}))
        res_f = self.client.get(reverse('pentestprojecthistory-finding', kwargs=url_kwargs | {'id': f.finding_id}))
        res_n = self.client.get(reverse('pentestprojecthistory-note', kwargs=url_kwargs | {'id': n.note_id}))
        assert res_s.status_code == res_f.status_code == res_n.status_code == 200
        assert res_s.data['assignee'] == res_f.data['assignee'] == res_n.data['assignee'] is None

    def test_bulk_edit_members_api(self):
        u2 = create_user()
        p = create_project(members=[self.user, u2])
        m1 = p.members.get(user=self.user)
        m2 = p.members.get(user=u2)

        # No changes => no history
        self.client.patch(reverse('pentestproject-detail', kwargs={'pk': p.id}), data={'members': [
            {'id': self.user.id, 'roles': ProjectMemberRole.default_roles},
            {'id': u2.id, 'roles': ProjectMemberRole.default_roles},
        ]})
        assert_history(m1, history_count=1, history_type='+')
        assert_history(m2, history_count=1, history_type='+')

        # add/delete member
        u3 = create_user()
        self.client.patch(reverse('pentestproject-detail', kwargs={'pk': p.id}), data={'members': [
            {'id': self.user.id, 'roles': ProjectMemberRole.default_roles},
            {'id': u3.id, 'roles': ProjectMemberRole.default_roles},
        ]})
        m3 = p.members.get(user=u3)
        assert_history(m1, history_count=1, history_type='+')
        assert_history(m2, history_count=2, history_type='-')
        assert_history(m3, history_count=1, history_type='+')

        # Update roles
        self.client.patch(reverse('pentestproject-detail', kwargs={'pk': p.id}), data={'members': [
            {'id': self.user.id, 'roles': ProjectMemberRole.default_roles},
            {'id': u3.id, 'roles': ['reviewer']},
        ]})
        assert_history(m1, history_count=1, history_type='+')
        assert_history(m3, history_count=2, history_type='~')

    def test_history_api_show_deleted(self):
        p = create_project(members=[self.user], findings_kwargs=[{'data': {'title': 'title'}}])
        f = p.findings.first()
        res_before_delete = self.client.get(reverse('finding-detail', kwargs={'project_pk': p.id, 'id': f.finding_id})).data
        f.history.all().delete()
        f.delete()

        # Historic record at delete time
        timeline = self.client.get(reverse('finding-history-timeline', kwargs={'project_pk': p.id, 'id': f.finding_id})).data['results']
        res_deleted = self.client.get(reverse('pentestprojecthistory-finding', kwargs={'project_pk': p.id, 'id': f.finding_id, 'history_date': timeline[0]['history_date']}))
        assert res_deleted.status_code == 200
        assert omit_keys(res_deleted.data, ['updated', 'lock_info']) == omit_keys(res_before_delete, ['updated', 'lock_info'])

        # Historic record after delete
        res_after_delete = self.client.get(reverse('pentestprojecthistory-finding', kwargs={'project_pk': p.id, 'id': f.finding_id, 'history_date': timezone.now().isoformat()}))
        assert res_after_delete.status_code == 404


@pytest.mark.django_db
class TestHistoryCleanup:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.u1 = create_user()
        self.u2 = create_user()

        with override_settings(SIMPLE_HISTORY_CLEANUP_TIMEFRAME=timedelta(hours=2)):
            yield

    def assert_history_cleanup(self, history_entries, pad=False, before=None):
        if pad:
            history_entries = \
                [{'history_type': '+', 'cleanup': False}] + \
                history_entries + \
                [{'history_type': '-', 'cleanup': False}]

        with mock_time(before=before if before is not None else timedelta(days=10)):
            finding = create_project(findings_kwargs=[{}]).findings.first()
            finding.history.all().delete()

            history_date = timezone.now()
            for h in history_entries:
                history_date += h.get('after', timedelta(seconds=5))
                h['instance'] = PentestFinding.history.create(
                    history_type=h.get('history_type', '~'),
                    history_date=history_date,
                    history_user=h.get('history_user', None),
                    history_prevent_cleanup=h.get('history_prevent_cleanup', False),
                    **{f.attname: getattr(finding, f.attname) for f in PentestFinding.history.model.tracked_fields},
                )

        async_to_sync(cleanup_history)(task_info={
            'model': PeriodicTask(last_success=None),
        })

        for h in history_entries:
            cleaned = not PentestFinding.history.filter(history_id=h['instance'].history_id).exists()
            assert cleaned == h['cleanup']

    def test_keep_create_delete(self):
        self.assert_history_cleanup([
            {'history_type': '+', 'cleanup': False},
            {'history_type': '~', 'cleanup': True},
            {'history_type': '-', 'cleanup': False},
        ], pad=True)

    def test_keep_first_last(self):
        self.assert_history_cleanup([
            {'history_type': '~', 'cleanup': False},
            {'history_type': '~', 'cleanup': True},
            {'history_type': '~', 'cleanup': True},
            {'history_type': '~', 'cleanup': False},
        ], pad=False)

    def test_keep_prevent_cleanup(self):
        self.assert_history_cleanup([
            {'cleanup': True},
            {'history_prevent_cleanup': True, 'cleanup': False},
            {'cleanup': True},
        ], pad=True)

    def test_keep_latest_before_pause(self):
        self.assert_history_cleanup([
            {'cleanup': True},
            {'cleanup': False},
            {'after': timedelta(days=1), 'cleanup': True},
            {'cleanup': True},
        ], pad=True)

    def test_keep_latest_before_pause_per_user(self):
        self.assert_history_cleanup([
            {'history_user': self.u1, 'cleanup': True},
            {'history_user': self.u2, 'cleanup': True},
            {'history_user': self.u1, 'cleanup': False},
            {'history_user': self.u2, 'cleanup': False},
            # pause
            {'history_user': self.u1, 'after': timedelta(days=1), 'cleanup': True},
            {'history_user': self.u2, 'cleanup': True},
            {'history_user': self.u1, 'cleanup': True},
            {'history_user': self.u2, 'cleanup': False},
            {'history_user': self.u1, 'cleanup': False},
        ], pad=True)

    def test_keep_latest_before_pause_per_user_per_window(self):
        self.assert_history_cleanup([
            {'history_user': self.u1, 'history_type': '+', 'cleanup': False},
            # window 1
            {'history_user': self.u1, 'cleanup': True},
            {'history_user': self.u2, 'cleanup': False},
            {'history_user': self.u1, 'history_prevent_cleanup': True, 'cleanup': False},
            # window 2
            {'history_user': self.u2, 'cleanup': False},
            {'history_user': self.u1, 'after': timedelta(days=1), 'cleanup': True},
            {'history_user': self.u2, 'cleanup': False},
            {'history_user': self.u1, 'history_prevent_cleanup': True, 'cleanup': False},
            # window 3
            {'history_user': self.u2, 'cleanup': True},
            {'history_user': self.u1, 'cleanup': True},
            {'history_user': self.u2, 'cleanup': False},
            {'history_user': self.u1, 'cleanup': False},
        ], pad=False)

    def test_keep_one_per_timeframe(self):
        # No cleanup in first 5 minutes
        self.assert_history_cleanup([
            {'after': timedelta(minutes=1), 'cleanup': False},
            {'after': timedelta(minutes=1), 'cleanup': False},
            {'after': timedelta(minutes=1), 'cleanup': False},
        ], pad=True, before=timedelta(minutes=0))

        # Keep one entry per 10 min timeframe in first 2 hours
        self.assert_history_cleanup([
            {'cleanup': True},
            {'after': timedelta(minutes=3), 'cleanup': True},
            {'after': timedelta(minutes=3), 'cleanup': True},
            {'after': timedelta(minutes=3), 'cleanup': False},
            {'after': timedelta(minutes=3), 'cleanup': True},
        ], pad=True, before=timedelta(hours=1))

        # Keep one entry per 30 min timeframe in first day
        self.assert_history_cleanup([
            {'cleanup': True},
            {'after': timedelta(minutes=9), 'cleanup': True},
            {'after': timedelta(minutes=9), 'cleanup': True},
            {'after': timedelta(minutes=9), 'cleanup': False},
            {'after': timedelta(minutes=9), 'cleanup': True},
        ], pad=True, before=timedelta(hours=10))

        # Keep one entry per 2 hour timeframe after first day
        self.assert_history_cleanup([
            {'cleanup': True},
            {'after': timedelta(minutes=45), 'cleanup': True},
            {'after': timedelta(minutes=45), 'cleanup': False},
            {'after': timedelta(minutes=45), 'cleanup': True},
            {'after': timedelta(minutes=45), 'cleanup': True},
        ], pad=True, before=timedelta(days=2))
