import pytest
import enum
from asgiref.sync import async_to_sync
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

from reportcreator_api.tests.mock import create_template_translation, create_user, api_client, create_template, create_project
from reportcreator_api.pentests.models import FindingTemplate, FindingTemplateTranslation, UploadedTemplateImage, \
    ReviewStatus, Language
from reportcreator_api.utils.utils import omit_keys


def has_changes(a, b):
    tracked_fields = a.tracked_fields if hasattr(a, 'tracked_fields') else a.history.model.tracked_fields if hasattr(a, 'history') else b.tracked_fields
    for f in tracked_fields:
        av = getattr(a, f.attname)
        bv = getattr(b, f.attname)
        if av != bv or \
           ((isinstance(av, enum.Enum) or isinstance(bv, enum.Enum)) and str(av) != str(bv)):
            return True
    return False


@pytest.mark.django_db
class TestTemplateHistory:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user(is_template_editor=True)
        self.client = api_client(self.user)

    def test_create_template_signal(self):
        t = FindingTemplate.objects.create(tags=['test'])
        assert t.history.all().count() == 1
        th = t.history.all()[0]
        assert th.history_type == '+'
        assert th.history_prevent_cleanup
        assert not has_changes(t, th)

    def test_create_translation_signal(self):
        t = create_template()
        tr = FindingTemplateTranslation.objects.create(template=t, language=Language.FRENCH, title='test')
        assert tr.history.all().count() == 1
        trh = tr.history.all()[0]
        assert trh.history_type == '+'
        assert trh.history_prevent_cleanup
        assert not has_changes(tr, trh)

    @pytest.mark.parametrize(['changes', 'change_reason'], [
        ({'status': ReviewStatus.FINISHED}, 'Status changed'),
        ({'language': Language.FRENCH}, 'Language changed'),
        ({'data': {'title': 'changed title'}}, None)
    ])
    def test_update_translation(self, changes, change_reason):
        t = create_template()
        tr = t.main_translation
        tr_initial = FindingTemplateTranslation.objects.get(id=tr.id)

        def reset_state():
            tr_initial.save()
            tr.history.all().delete()

        def assert_history(api=False):
            tr.refresh_from_db()
            assert tr.history.all().count() == 1
            trh = tr.history.all()[0]
            assert trh.history_type == '~'
            assert trh.history_change_reason == change_reason
            if api:
                assert trh.history_user == self.user
            
            trh = tr.history.most_recent()
            assert not has_changes(tr, trh)

        # Signal
        reset_state()
        for k, v in changes.items():
            if k == 'data':
                tr.update_data(v)
            else:
                setattr(tr, k, v)
        tr.save()
        assert_history(api=False)

        # API translation detail
        reset_state()
        self.client.patch(reverse('findingtemplatetranslation-detail', kwargs={'template_pk': t.id, 'pk': tr.id}), data=changes)
        assert_history(api=True)

        # API template sublist
        reset_state()
        data = self.client.get(reverse('findingtemplate-detail', kwargs={'pk': t.id})).data
        data['translations'][0].update(changes)
        self.client.patch(reverse('findingtemplate-detail', kwargs={'pk': t.id}), data=data)
        assert_history(api=True)

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
        assert tr.history.all().count() == 2
        trh = tr.history.all()[0]
        assert trh.history_type == '-'
        assert not has_changes(tr, trh)

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
                {'is_main': True, 'language': Language.ENGLISH, 'data': {'title': 'test'}},
                {'is_main': False, 'language': Language.GERMAN, 'data': {'title': 'test'}},
            ],
        })
        assert res.status_code == 201
        t = FindingTemplate.objects.get(id=res.data['id'])
        tr1 = t.translations.all()[0]
        tr2 = t.translations.all()[1]
        assert t.history.count() == tr1.history.count() == tr2.history.count() == 1

        th = t.history.all()[0]
        trh1 = tr1.history.all()[0]
        trh2 = tr2.history.all()[0]
        assert th.history_type == trh1.history_type == trh2.history_type == '+'
        assert th.history_date == trh1.history_date == trh2.history_date
        assert not has_changes(t, th)
        assert not has_changes(tr1, trh1)
        assert not has_changes(tr2, trh2)
    
    def test_create_from_finding_api(self):
        project = create_project(members=[self.user], findings_kwargs=[{
            'data': {
                'title': 'finding title',
                'description': '![image](/images/name/image.png)',
            }
        }], images_kwargs=[{'name': 'image.png'}, {'name': 'image_unreferenced.png'}])
        finding = project.findings.first()
        data = self.client.post(reverse('findingtemplate-fromfinding'), data={
            'project': project.id,
            'translations': [
                {'is_main': True, 'language': project.language, 'data': finding.data}
            ]
        }).data
        t = FindingTemplate.objects.get(id=data['id'])
        tr = t.main_translation
        assert t.history.all().count() == tr.history.all().count() == 1
        th = t.history.all()[0]
        trh = t.history.all()[0]
        assert th.history_date == trh.history_date

    def test_update_template_api(self):
        t = create_template(tags=['test'], data={'title': 'test'}, translations_kwargs=[{'language': Language.GERMAN, 'data': {'title': 'test'}}])
        tr1 = t.main_translation
        tr2 = t.translations.get(language=Language.GERMAN)

        # Update without changes: no history
        res = self.client.patch(reverse('findingtemplate-detail', kwargs={'pk': t.id}), data=self.client.get(reverse('findingtemplate-detail', kwargs={'pk': t.id})).data)
        assert res.status_code == 200
        assert t.history.all().count() == tr1.history.all().count() == tr2.history.all().count() == 1
        assert t.history.all()[0].history_type == tr1.history.all()[0].history_type == tr2.history.all()[0].history_type == '+'

        # Create translation
        data = self.client.get(reverse('findingtemplate-detail', kwargs={'pk': t.id})).data
        data['translations'].append({'language': Language.SPANISH})
        res = self.client.patch(reverse('findingtemplate-detail', kwargs={'pk': t.id}), data=data)
        assert res.status_code == 200
        tr3 = t.translations.get(language=Language.SPANISH)
        assert tr3.history.all().count() == 1
        tr3h = tr3.history.all()[0]
        assert tr3h.history_type == '+'
        assert tr3h.history_user == self.user

        # Delete translation
        data['translations'] = [tr for tr in data['translations'] if tr['language'] != Language.SPANISH]
        res = self.client.patch(reverse('findingtemplate-detail', kwargs={'pk': t.id}), data=data)
        assert res.status_code == 200
        assert tr3.history.all().count() == 2
        tr3h = tr3.history.all()[0]
        assert tr3h.history_type == '-'
        assert tr3h.history_user == self.user

        # Update template tags
        data['tags'].append('new')
        res = self.client.patch(reverse('findingtemplate-detail', kwargs={'pk': t.id}), data=data)
        assert res.status_code == 200
        assert t.history.all().count() == 2
        th = t.history.all()[0]
        assert th.history_type == '~'
        assert th.history_change_reason is None
        assert th.history_user == self.user

        # Change main_translation
        data['translations'][0]['is_main'] = False
        data['translations'][1]['is_main'] = True
        res = self.client.patch(reverse('findingtemplate-detail', kwargs={'pk': t.id}), data=data)
        assert res.status_code == 200
        assert t.history.all().count() == 3
        th = t.history.all()[0]
        assert th.history_type == '~'
        assert th.history_change_reason == 'Main translation changed'
        assert th.history_user == self.user

        assert tr1.history.all().count() == tr2.history.all().count() == 1
        assert tr1.history.all()[0].history_type == tr2.history.all()[0].history_type == '+'

    def format_template(self, template_data):
        out = omit_keys(template_data, ['updated', 'lock_info', 'usage_count'])
        out['translations'] = sorted([omit_keys(tr, ['updated']) for tr in out.get('translations', [])], key=lambda tr: tr['id'])
        return out

    def test_history_api(self):
        t = create_template(language=Language.ENGLISH, tags=['tag1'], data={'title': 'title 1'}, translations_kwargs=[], images_kwargs=[])
        tr1 = t.main_translation
        history = []

        def add_history_test():
            history.append({
                'history_date': timezone.now(),
                'template': self.client.get(reverse('findingtemplate-detail', kwargs={'pk': t.id})).data,
                'images': {i.name: i.file.read() for i in t.images.all()}
            })

        # Initial template
        add_history_test()
        # Upload image
        ti1 = UploadedTemplateImage.objects.create(linked_object=t, name='file1.png', file=SimpleUploadedFile(name=f'file1.png', content=b'file1'))
        add_history_test()
        # Add translation
        tr2 = create_template_translation(template=t, language=Language.GERMAN, data={'title': 'title 2'})
        add_history_test()
        # Update template and translation
        t.tags = ['tag2']
        t.save()
        tr1.update_data({'title': 'title 1 updated'})
        tr1.save()
        add_history_test()
        # Replace image
        ti1.delete()
        UploadedTemplateImage.objects.create(linked_object=t, name='file1.png', file=SimpleUploadedFile(name=f'file1.png', content=b'file2'))
        add_history_test()
        # Change main translation
        t.main_translation = tr2
        t.save()
        tr1.delete()
        add_history_test()

        # TODO: test template timeline and translation timeline entries

        # Test history entries
        for h in history:
            res_t = self.client.get(reverse('templatehistory-detail', kwargs={'template_pk': t.id, 'history_date': h['history_date'].isoformat()}))
            assert res_t.status_code == 200
            assert self.format_template(res_t.data) == self.format_template(h['template'])
            for name, content in h['images'].items():
                res_i = self.client.get(reverse('templatehistory-image-by-name', kwargs={'template_pk': t.id, 'history_date': h['history_date'].isoformat(), 'filename': name}))
                assert res_i.status_code == 200
                assert b''.join(iter(res_i)) == content
            
