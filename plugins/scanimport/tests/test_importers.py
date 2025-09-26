import textwrap
from pathlib import Path

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import serializers
from sysreptor.pentests.models import Language
from sysreptor.tests.mock import (
    api_client,
    create_project,
    create_template,
    create_user,
    override_configuration,
    update,
)
from sysreptor.tests.utils import assertKeysEqual

from ..apps import ScanImportPluginConfig
from ..importers import registry
from ..importers.base import BaseImporter

SCANIMPORT_APPLABEL = ScanImportPluginConfig.label
DATA_FILES = [f for f in (Path(__file__).parent / 'data').glob('**/*') if f.is_file()]


@pytest.mark.django_db
class TestImporters:
    @pytest.fixture(autouse=True)
    def setUp(self):
        user = create_user()
        self.project = create_project(members=[user])
        self.client = api_client(user)

    @pytest.mark.parametrize('file', DATA_FILES)
    def test_format_detection(self, file):
        with file.open('rb') as f:
            assert registry.auto_detect_format(f).id == file.parent.name

    @pytest.mark.parametrize('file', DATA_FILES)
    def test_import_notes(self, file):
        with file.open('rb') as f:
            notes = registry.get(file.parent.name).parse_notes(files=[f])
        assert len(notes) > 0
        assert notes[0].title.lower() == file.parent.name

    @pytest.mark.parametrize('file', DATA_FILES)
    def test_import_findings(self, file):
        importer = registry.get(file.parent.name)
        with file.open('rb') as f:
            findings = importer.parse_findings(files=[f], project=self.project)
        if importer.id in ['nmap', 'zap']:
            assert len(findings) == 0
        else:
            assert len(findings) > 0

    @pytest.mark.parametrize('import_as', ['notes', 'findings'])
    def test_import_multiple(self, import_as):
        res = self.client.post(reverse(f'{SCANIMPORT_APPLABEL}:parse', kwargs={'project_pk': self.project.id}), data={
            'file': [f.open('rb') for f in DATA_FILES],
            'import_as': import_as,
            'importer': 'auto',
        }, format='multipart')
        assert res.status_code == 200, res.data
        assert len(res.data) > 0

    def test_unsupported_file_format(self):
        unsupported_file = SimpleUploadedFile("test.txt", b"This is not a scan file", content_type="text/plain")
        res = self.client.post(reverse(f'{SCANIMPORT_APPLABEL}:parse', kwargs={'project_pk': self.project.id}), data={
            'file': [unsupported_file],
            'import_as': 'findings',
            'importer': 'auto',
        }, format='multipart')
        assert res.status_code == 400


@pytest.mark.django_db
class TestTemplateRendering:
    @pytest.fixture(autouse=True)
    def setUp(self):
        user = create_user()
        self.project = create_project(members=[user])
        self.client = api_client(user)

    def import_burp_finding(self):
        with next(f for f in DATA_FILES if f.name == 'burp.xml').open('rb') as f:
            res = self.client.post(reverse(f'{SCANIMPORT_APPLABEL}:parse', kwargs={'project_pk': self.project.id}), data={
                'file': [f],
                'import_as': 'findings',
                'importer': 'burp',
            }, format='multipart')
        assert res.status_code == 200, res.data
        return next(f for f in res.data if 'scanimport:burp:2097936' in f['template_info']['search_path'])

    def test_template_selection_fallback(self):
        f = self.import_burp_finding()
        assert not f['template']
        assert f['template_info']['is_fallback']
        assert f['template_info']['search_path'] == ['scanimport:burp:2097936', 'scanimport:burp']
    
    def test_template_selection_general(self):
        t = create_template(tags=['scanimport:burp'], data={'title': 'Override title', 'description': 'Override description'})
        f = self.import_burp_finding()
        assert f['template'] == t.id
        assert not f['template_info']['is_fallback']
        assertKeysEqual(f['data'], t.main_translation.data, ['title', 'description'])
    
    def test_template_selection_specific(self):
        create_template(tags=['scanimport:burp'], data={'title': 'No match title', 'description': 'No match description'})
        t = create_template(tags=['scanimport:burp:2097936'], data={'title': 'Override title', 'description': 'Override description'})
        f = self.import_burp_finding()
        assert f['template'] == t.id
        assert not f['template_info']['is_fallback']
        assertKeysEqual(f['data'], t.main_translation.data, ['title', 'description'])
    
    def test_template_selection_no_match(self):
        t = create_template(tags=['scanimport:burp:nomatch'], data={'title': 'No match'})
        f = self.import_burp_finding()
        assert not f['template']
        assert f['template_info']['is_fallback']
        assert f['data']['title'] != t.main_translation.data['title']
    
    def test_template_selection_language(self):
        update(self.project, language=Language.GERMAN_DE)
        t = create_template(tags=['scanimport:burp'], 
                            data={'title': 'EN title', 'description': 'EN description'}, language=Language.ENGLISH_US,
                            translations_kwargs=[{'data': {'title': 'DE title', 'description': 'DE description'}, 'language': Language.GERMAN_DE}])
        f = self.import_burp_finding()
        assert f['template'] == t.id
        assert not f['template_info']['is_fallback']
        assert f['template_info']['language'] == Language.GERMAN_DE
        assertKeysEqual(f['data'], t.translations.get(language=Language.GERMAN_DE).data, ['title', 'description'])

    def test_django_template_language(self):
        t = create_template(tags=['scanimport:burp'], data={
            'description': textwrap.dedent(
                """\
                <!--{% noemptylines %}-->
                <!--{{ title }}-->

                <!--{% if severity == 'high' %}-->If<!--{% endif %}-->

                <!--{% for a in affected_components %}-->
                * <!--{{ a }}--> in For-loop
                <!--{% endfor %}-->
                <!--{% endnoemptylines %}-->
                """
            )
        })
        f = self.import_burp_finding()
        assert f['template'] == t.id
        assert f['data']['description'] == textwrap.dedent(
            """\
            Cross-site scripting (DOM-based)
            If
            * https://ginandjuice.shop/blog/ in For-loop
            """
        )

    @pytest.mark.parametrize(('template_str', 'expected'), [
        ('<!--{{ variable_string }}-->', 'variable_string'),
        ('<!--{{ variable_list }}-->', "['item1', 'item2']"),
        ('<!--{{ variable_dict }}-->', "{'key': 'value'}"),
        ('<!--{{ variable_dict.key }}-->', 'value'),
        ('<!--{{ variable_none }}-->', 'None'),
        ('<!--{{ variable_missing }}-->', ''),
        ('<!--{{ missing.nested.variable }}-->', ''),
        ('<!--{% for i in variable_list %}--><!--{{ i }}-->;<!--{% endfor %}-->', 'item1;item2;'),
        ('<!--{% for i in variable_string %}--><!--{{ i }}-->;<!--{% endfor %}-->', 'v;a;r;i;a;b;l;e;_;s;t;r;i;n;g;'),
        ('<!--{% for i in variable_none %}--><!--{{ i }}-->;<!--{% endfor %}-->', ''),
        ('<!--{% for i in variable_missing %}--><!--{{ i }}-->;<!--{% endfor %}-->', ''),
        ('<!--{% for k, v in variable_dict.items %}--><!--{{ k }}-->=<!--{{ v }}-->;<!--{% endfor %}-->', 'key=value;'),
        ('<!--{% for k, v in variable_none.items %}--><!--{{ k }}-->=<!--{{ v }}-->;<!--{% endfor %}-->', ''),
        ('<!--{% for k, v in variable_missing.items %}--><!--{{ k }}-->=<!--{{ v }}-->;<!--{% endfor %}-->', ''),
    ])
    def test_template_ignored_errors(self, template_str, expected):
        t = create_template(data={'description': template_str})
        f = BaseImporter().generate_finding_from_template(project=self.project, tr=t.main_translation, data={
            'variable_string': 'variable_string',
            'variable_list': ['item1', 'item2'],
            'variable_dict': {'key': 'value'},
            'variable_none': None,
        })
        assert f.data['description'] == expected

    def test_template_syntax_error(self):
        t = create_template(tags=['scanimport:burp'], data={'description': 'Syntax error: <!--{% for i in list %}-->no endfor'})
        with pytest.raises(serializers.ValidationError) as exc_info:
            BaseImporter().generate_finding_from_template(project=self.project, tr=t.main_translation, data={})
        assert 'Template error' in str(exc_info.value)
        assert 'description' in str(exc_info.value)

    def test_template_data_field_priority(self):
        t = create_template(data={'title': 'template_value', 'field_string': 'template_value', 'field_int': 100})
        data = {'title': 'Parsed Title', 'field_string': 'parsed_value', 'field_int': 50, 'field_list': ['parsed_value']}
        f = BaseImporter().generate_finding_from_template(project=self.project, tr=t.main_translation, data=data)
        
        assertKeysEqual(f.data, t.main_translation.data, ['title', 'field_string', 'field_int'])
        assertKeysEqual(f.data, data, ['field_list'])

    @pytest.mark.parametrize(('data', 'expected'), [
        ({'field_string': 'string'}, {'field_string': 'string'}),
        ({'field_list': ['list']}, {'field_list': ['list']}),
        ({'field_string': ['list']}, {'field_string': 'list'}),
        ({'field_list': 'string'}, {'field_list': ['string']}),
        ({'field_string': None}, {'field_string': None}),
        ({'field_list': None}, {'field_list': []}),
    ])
    def test_incompatible_field_types(self, data, expected):
        f = BaseImporter().generate_finding_from_template(
            project=self.project, 
            tr=create_template().main_translation, 
            data=data)
        assertKeysEqual(f.data, expected, expected.keys())


@pytest.mark.django_db
class TestAPIPermissions:
    @pytest.mark.parametrize(('user_name', 'project_name', 'expected'), [
        ('member', 'project', True),
        ('guest', 'project', False),
        ('admin', 'project', True),
        ('unauthorized', 'project', False),
        ('anonymous', 'project', False),
        ('member', 'readonly', False),
        ('guest', 'readonly', False),
        ('admin', 'readonly', False),
    ])
    def test_permissions(self, user_name, project_name, expected):
        user_member = create_user()
        user_guest = create_user(is_guest=True)
        users = {
            'member': user_member,
            'guest': user_guest,
            'admin': create_user(is_superuser=True),
            'unauthorized': create_user(),
            'anonymous': AnonymousUser(),
        }
        user = users[user_name]
        if user.is_superuser:
            user.admin_permissions_enabled = True

        projects = {
            'project': create_project(members=[user_member, user_guest]),
            'readonly': create_project(members=[user_member, user_guest], readonly=True),
        }
        project = projects[project_name]
        
        with override_configuration(GUEST_USERS_CAN_EDIT_PROJECTS=False):
            res = api_client(user).post(reverse(f'{SCANIMPORT_APPLABEL}:parse', kwargs={'project_pk': project.id}), data={
                'file': [next(f for f in DATA_FILES if f.name == 'burp.xml').open('rb')],
                'import_as': 'findings',
                'importer': 'auto',
            }, format='multipart')
            assert res.status_code in ([200] if expected else [403, 404])
