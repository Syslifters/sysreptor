import textwrap
from pathlib import Path

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
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

    def test_template_missing_context_variables(self):
        create_template(tags=['scanimport:burp'], data={'description': 'Missing variable: <!--{{ missing.nested.variable }}-->'})
        f = self.import_burp_finding()
        assert f['data']['description'] == 'Missing variable: '


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
