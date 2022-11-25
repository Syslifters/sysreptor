import pytest
from django.urls import reverse
from django.core.files.base import ContentFile
from django.http import FileResponse, StreamingHttpResponse
from django.test import override_settings
from rest_framework.test import APIClient
from reportcreator_api.pentests.models import ProjectType, FindingTemplate, PentestProject
from reportcreator_api.tests.mock import create_user, create_project, create_project_type, create_template, create_png_file
from reportcreator_api.archive.import_export import export_project_types, export_projects, export_templates


def export_archive(obj):
    if isinstance(obj, ProjectType):
        exp = export_project_types([obj])
    elif isinstance(obj, FindingTemplate):
        exp = export_templates([obj])
    elif isinstance(obj, PentestProject):
        exp = export_projects([obj])
    return ContentFile(content=b''.join(exp), name='export.tar.gz')


def viewset_urls(basename, get_kwargs, create_data={}, list=False, retrieve=False, create=False, update=False, update_partial=False, delete=False, lock=False, unlock=False):
    list_urlname = basename + '-list'
    detail_urlname = basename + '-detail'

    out = []
    if list:
        out.append((basename + ' list', lambda s, c: c.get(reverse(list_urlname, kwargs=get_kwargs(s, False)))))
    if retrieve:
        out.append((basename + ' retrieve', lambda s, c: c.get(reverse(detail_urlname, kwargs=get_kwargs(s, True)))))
    if create:
        out.append((basename + ' create', lambda s, c: c.post(reverse(list_urlname, kwargs=get_kwargs(s, False)), data=c.get(reverse(detail_urlname, kwargs=get_kwargs(s, True))).data | create_data)))
    if update:
        out.append((basename + ' update', lambda s, c: c.put(reverse(detail_urlname, kwargs=get_kwargs(s, True)), data=c.get(reverse(detail_urlname, kwargs=get_kwargs(s, True))).data)))
    if update_partial:
        out.append((basename + ' partial_update', lambda s, c: c.patch(reverse(detail_urlname, kwargs=get_kwargs(s, True)), data=c.get(reverse(detail_urlname, kwargs=get_kwargs(s, True))).data)))
    if delete:
        out.append((basename + ' delete', lambda s, c: c.delete(reverse(detail_urlname, kwargs=get_kwargs(s, True)))))
    if lock:
        out.append((basename + ' lock', lambda s, c: c.post(reverse(basename + '-lock', kwargs=get_kwargs(s, True)), data={})))
    if unlock:
        out.append((basename + ' unlock', lambda s, c: c.post(reverse(basename + '-unlock', kwargs=get_kwargs(s, True)), data={})))
    return out


def file_viewset_urls(basename, get_obj, get_base_kwargs=None, read=False, write=False):
    get_base_kwargs = get_base_kwargs or (lambda s: {})
    def get_kwargs(s, detail):
        obj = get_obj(s)
        return get_base_kwargs(s) | ({'filename': obj.name} if detail == 'name' else {'pk': obj.pk} if detail else {})

    out = viewset_urls(basename=basename, get_kwargs=get_kwargs, retrieve=read, update_partial=write, delete=write)
    if read:
        out.append((basename + ' retrieve-by-name', lambda s, c: c.get(reverse(basename + '-retrieve-by-name', kwargs=get_kwargs(s, 'name')))))
    if write:
        out.extend([
            (basename + ' create', lambda s, c: c.post(
                path=reverse(basename + '-list', kwargs=get_kwargs(s, False)), 
                data={'name': 'image.png', 'file': ContentFile(name='image.png', content=create_png_file())},
                format='multipart',
            )),
            (basename + ' update', lambda s, c: c.put(
                path=reverse(basename + '-detail', kwargs=get_kwargs(s, True)),
                data={'name': 'image.png', 'file': ContentFile(name='image2.png', content=create_png_file())},
                format='multipart'
            )),
        ])
    return out


def project_viewset_urls(get_obj, read=False, write=False, create=False, list=False):
    out = [
        *viewset_urls('pentestproject', get_kwargs=lambda s, detail: {'pk': get_obj(s).pk} if detail else {}, list=list, retrieve=read, create=create, update=write, update_partial=write, delete=write),
        *viewset_urls('section', get_kwargs=lambda s, detail: {'project_pk': get_obj(s).pk} | ({'section_id': get_obj(s).sections.first().section_id} if detail else {}), list=read, retrieve=read, update=write, update_partial=write, lock=write, unlock=write),
        *viewset_urls('finding', get_kwargs=lambda s, detail: {'project_pk': get_obj(s).pk} | ({'finding_id': get_obj(s).findings.first().finding_id} if detail else {}), list=read, retrieve=read, create=write, delete=write, update=write, update_partial=write, lock=write, unlock=write),
        *file_viewset_urls('uploadedimage', get_base_kwargs=lambda s: {'project_pk': get_obj(s).pk}, get_obj=lambda s: get_obj(s).images.first(), read=read, write=write),
    ]
    if read:
        out.extend([
            ('pentestproject check', lambda s, c: c.get(reverse('pentestproject-check', kwargs={'pk': get_obj(s).pk}))),
            ('pentestproject export', lambda s, c: c.post(reverse('pentestproject-export', kwargs={'pk': get_obj(s).pk}))),
            ('pentestproject preview', lambda s, c: c.post(reverse('pentestproject-preview', kwargs={'pk': get_obj(s).pk}), data={})),
            ('pentestproject generate', lambda s, c: c.post(reverse('pentestproject-generate', kwargs={'pk': get_obj(s).pk}), data={'password': 'pdf-password'})),
        ])
    if create:
        out.extend([
            ('pentestproject import', lambda s, c: c.post(reverse('pentestproject-import'), data={'file': export_archive(get_obj(s))}, format='multipart')),
            ('pentestproject copy', lambda s, c: c.post(reverse('pentestproject-copy', kwargs={'pk': get_obj(s).pk}), data={})),
            ('pentestproject finding-fromtemplate', lambda s, c: c.post(reverse('finding-fromtemplate', kwargs={'project_pk': get_obj(s).pk}), data={'template': s.template.pk})),
        ])
    return out


def expect_result(urls, allowed_users=None):
    all_users = {'public', 'regular', 'template_editor', 'designer', 'user_manager', 'superuser'}

    for user in allowed_users or []:
        yield from [(user, *u, True) for u in urls]
    for user in all_users - set(allowed_users):
        yield from [(user, *u, False) for u in urls]


@pytest.mark.django_db
class TestApiRequestsAndPermissions:
    @staticmethod
    def public_urls():
        return [
            ('utils healthcheck', lambda s, c: c.get(reverse('utils-healthcheck'))),
        ]

    @staticmethod
    def regular_user_urls():
        return [
            ('utils list', lambda s, c: c.get(reverse('utils-list'))),
            ('utils languages', lambda s, c: c.get(reverse('utils-languages'))),

            *viewset_urls('pentestuser', get_kwargs=lambda s, detail: {'pk': s.user_other.pk} if detail else {}, list=True, retrieve=True),
            *viewset_urls('pentestuser', get_kwargs=lambda s, detail: {'pk': 'self'}, retrieve=True, update=True, update_partial=True),

            *viewset_urls('findingtemplate', get_kwargs=lambda s, detail: {'pk': s.template.pk} if detail else {}, list=True, retrieve=True),
            ('findingtemplate fielddefinition', lambda s, c: c.get(reverse('findingtemplate-fielddefinition'))),

            *viewset_urls('projecttype', get_kwargs=lambda s, detail: {'pk': s.project_type.pk} if detail else {}, list=True, retrieve=True),
            *file_viewset_urls('uploadedasset', get_base_kwargs=lambda s: {'projecttype_pk': s.project_type.pk}, get_obj=lambda s: s.project_type_asset, read=True),
            ('projecttype get-predefined-finding-fields', lambda s, c: c.get(reverse('projecttype-get-predefined-finding-fields'))),
            ('projecttype preview', lambda s, c: c.post(reverse('projecttype-preview', kwargs={'pk': s.project_type.pk}), data={'report_template': '', 'report_styles': '', 'report_preview_data': {}})),

            *project_viewset_urls(get_obj=lambda s: s.project, list=True, read=True, create=True, write=True),
            *project_viewset_urls(get_obj=lambda s: s.project_readonly, read=True),
            ('pentestproject readonly', lambda s, c: c.put(reverse('pentestproject-readonly', kwargs={'pk': s.project.pk}), data={'readonly': True})),
            ('pentestproject readonly', lambda s, c: c.put(reverse('pentestproject-readonly', kwargs={'pk': s.project_readonly.pk}), data={'readonly': False})),
        ]

    @staticmethod
    def template_editor_urls():
        return {
            *viewset_urls('findingtemplate', get_kwargs=lambda s, detail: {'pk': s.template.pk} if detail else {}, create=True, update=True, update_partial=True, delete=True, lock=True, unlock=True),
            ('findingtemplate export', lambda s, c: c.post(reverse('findingtemplate-export', kwargs={'pk': s.template.pk}))),
            ('findingtemplate import', lambda s, c: c.post(reverse('findingtemplate-import'), data={'file': export_archive(s.template)}, format='multipart')),
        }
    
    @staticmethod
    def designer_urls():
        return [
            *viewset_urls('projecttype', get_kwargs=lambda s, detail: {'pk': s.project_type.pk} if detail else {}, create=True, update=True, update_partial=True, delete=True, lock=True, unlock=True),
            *file_viewset_urls('uploadedasset', get_base_kwargs=lambda s: {'projecttype_pk': s.project_type.pk}, get_obj=lambda s: s.project_type_asset, write=True),
            ('projecttype copy', lambda s, c: c.post(reverse('projecttype-copy', kwargs={'pk': s.project_type.pk}))),
            ('projecttype export', lambda s, c: c.post(reverse('projecttype-export', kwargs={'pk': s.project_type.pk}))),
            ('projecttype import', lambda s, c: c.post(reverse('projecttype-import'), data={'file': export_archive(s.project_type)}, format='multipart')),
        ]

    @staticmethod
    def user_manager_urls():
        return [
            *viewset_urls('pentestuser', get_kwargs=lambda s, detail: {'pk': s.user_other.pk} if detail else {}, create=True, create_data={'username': 'other', 'password': 'D40C4dEyH9Naam6!'}, update=True, update_partial=True),
            ('pentestuser reset-password', lambda s, c: c.post(reverse('pentestuser-reset-password', kwargs={'pk': s.user_other.pk}), data={'password': 'D40C4dEyH9Naam6!'})),
        ]

    @staticmethod
    def superuser_urls():
        return [
            ('utils backup', lambda s, c: c.post(reverse('utils-backup'), data={'key': s.backup_key})),

            *project_viewset_urls(get_obj=lambda s: s.project_unauthorized, read=True, write=True),
        ]
    
    @staticmethod
    def forbidden_urls():
        return [
            *project_viewset_urls(get_obj=lambda s: s.project_readonly, write=True),
        ]

    @staticmethod
    def build_test_parameters():
        yield from expect_result(
            urls=TestApiRequestsAndPermissions.regular_user_urls(), 
            allowed_users=['regular', 'template_editor', 'designer', 'user_manager', 'superuser'],
        )
        yield from expect_result(
            urls=TestApiRequestsAndPermissions.template_editor_urls(), 
            allowed_users=['template_editor', 'superuser'], 
        )
        yield from expect_result(
            urls=TestApiRequestsAndPermissions.designer_urls(), 
            allowed_users=['designer', 'superuser'], 
        )
        yield from expect_result(
            urls=TestApiRequestsAndPermissions.user_manager_urls(), 
            allowed_users=['user_manager', 'superuser'], 
        )
        yield from expect_result(
            urls=TestApiRequestsAndPermissions.superuser_urls(), 
            allowed_users=['superuser'], 
        )
        yield from expect_result(
            urls=TestApiRequestsAndPermissions.forbidden_urls(),
            allowed_users=[],
        )

    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user_regular = create_user(username='regular')
        self.user_template_editor = create_user(username='template_editor', is_template_editor=True)
        self.user_designer = create_user(username='designer', is_designer=True)
        self.user_user_manager = create_user(username='user_manager', is_user_manager=True)
        self.user_superuser = create_user(username='superuser', is_superuser=True, is_staff=True)
        self.user_map = {
            'regular': self.user_regular,
            'template_editor': self.user_template_editor,
            'designer': self.user_designer,
            'user_manager': self.user_user_manager,
            'superuser': self.user_superuser,
        }

        self.user_other = create_user()

        self.project_type = create_project_type()
        self.project_type_asset = self.project_type.assets.first()
    
        self.project = create_project(pentesters=self.user_map.values())
        self.project_section = self.project.sections.first()
        self.project_finding = self.project.findings.first()
        self.project_image = self.project.images.first()

        self.project_readonly = create_project(pentesters=self.user_map.values(), readonly=True)
        self.project_readonly_section = self.project_readonly.sections.first()
        self.project_readonly_finding = self.project_readonly.findings.first()
        self.project_readonly_image = self.project_readonly.images.first()

        self.project_unauthorized = create_project()
        self.project_unauthorized_section = self.project_unauthorized.sections.first()
        self.project_unauthorized_finding = self.project_unauthorized.findings.first()
        self.project_unauthorized_image = self.project_unauthorized.images.first()

        self.template = create_template()

        self.backup_key = 'a' * 30
        with override_settings(BACKUP_KEY=self.backup_key):
            yield

    @pytest.mark.parametrize('user,name,perform_request,expected', build_test_parameters())
    def test_api_requests(self, user, name, perform_request, expected):
        client = APIClient()
        if user_obj := self.user_map.get(user):
            client.force_authenticate(user_obj)

        res = perform_request(self, client)
        info = res.data if not isinstance(res, (FileResponse, StreamingHttpResponse)) else res
        if expected:
            assert 200 <= res.status_code < 300, {'message': 'API request failed, but should have succeeded', 'info': info}
        else:
            assert 400 <= res.status_code < 500, {'message': 'API request succeeded, but should have failed', 'info': info}
