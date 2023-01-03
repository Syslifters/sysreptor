import pytest
from django.urls import reverse
from django.core.files.base import ContentFile
from django.http import FileResponse, StreamingHttpResponse
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from reportcreator_api.pentests.models import ProjectType, FindingTemplate, PentestProject, SourceEnum
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


def viewset_urls(basename, get_kwargs, create_data={}, list=False, retrieve=False, create=False, update=False, update_partial=False, destroy=False, lock=False, unlock=False):
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
    if destroy:
        out.append((basename + ' destroy', lambda s, c: c.delete(reverse(detail_urlname, kwargs=get_kwargs(s, True)))))
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

    out = viewset_urls(basename=basename, get_kwargs=get_kwargs, retrieve=read, update_partial=write, destroy=write)
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


def project_viewset_urls(get_obj, read=False, write=False, create=False, list=False, destory=None, update=None):
    destory = destory if destory is not None else write
    update = update if update is not None else write

    out = [
        *viewset_urls('pentestproject', get_kwargs=lambda s, detail: {'pk': get_obj(s).pk} if detail else {}, list=list, retrieve=read, create=create, update=update, update_partial=update, destroy=destory),
        *viewset_urls('section', get_kwargs=lambda s, detail: {'project_pk': get_obj(s).pk} | ({'section_id': get_obj(s).sections.first().section_id} if detail else {}), list=read, retrieve=read, update=write, update_partial=write, lock=write, unlock=write),
        *viewset_urls('finding', get_kwargs=lambda s, detail: {'project_pk': get_obj(s).pk} | ({'finding_id': get_obj(s).findings.first().finding_id} if detail else {}), list=read, retrieve=read, create=write, destroy=write, update=write, update_partial=write, lock=write, unlock=write),
        *file_viewset_urls('uploadedimage', get_base_kwargs=lambda s: {'project_pk': get_obj(s).pk}, get_obj=lambda s: get_obj(s).images.first(), read=read, write=write),
    ]
    if read:
        out.extend([
            ('pentestproject check', lambda s, c: c.get(reverse('pentestproject-check', kwargs={'pk': get_obj(s).pk}))),
            ('pentestproject export', lambda s, c: c.post(reverse('pentestproject-export', kwargs={'pk': get_obj(s).pk}))),
            ('pentestproject preview', lambda s, c: c.post(reverse('pentestproject-preview', kwargs={'pk': get_obj(s).pk}), data={})),
            ('pentestproject generate', lambda s, c: c.post(reverse('pentestproject-generate', kwargs={'pk': get_obj(s).pk}), data={'password': 'pdf-password'})),
        ])
    if write:
        out.extend([
            ('pentestproject finding-fromtemplate', lambda s, c: c.post(reverse('finding-fromtemplate', kwargs={'project_pk': get_obj(s).pk}), data={'template': s.template.pk})),
        ])
    if update:
        out.extend([
            ('pentestproject customize-projecttype', lambda s, c: c.post(reverse('pentestproject-customize-projecttype', kwargs={'pk': get_obj(s).pk}), data={'project_type': get_obj(s).project_type.id})),
        ])
    if create:
        out.extend([
            ('pentestproject copy', lambda s, c: c.post(reverse('pentestproject-copy', kwargs={'pk': get_obj(s).pk}), data={})),
            ('pentestproject import', lambda s, c: c.post(reverse('pentestproject-import'), data={'file': export_archive(get_obj(s))}, format='multipart')),
        ])
    return out


def projecttype_viewset_urls(get_obj, read=False, write=False, create=False, list=False):
    out = [
        *viewset_urls('projecttype', get_kwargs=lambda s, detail: {'pk': get_obj(s).pk} if detail else {}, list=list, retrieve=read, create=create, update=write, update_partial=write, destroy=write, lock=write, unlock=write),
        *file_viewset_urls('uploadedasset', get_base_kwargs=lambda s: {'projecttype_pk': get_obj(s).pk}, get_obj=lambda s: get_obj(s).assets.first(), read=read, write=write),
    ]
    if read:
        out.extend([
            ('projecttype preview', lambda s, c: c.post(reverse('projecttype-preview', kwargs={'pk': get_obj(s).pk}), data={'report_template': '', 'report_styles': '', 'report_preview_data': {}})),
        ])
    if write:
        out.extend([
            ('projecttype export', lambda s, c: c.post(reverse('projecttype-export', kwargs={'pk': get_obj(s).pk}))),
        ])
    if create:
        out.extend([
            ('projecttype copy', lambda s, c: c.post(reverse('projecttype-copy', kwargs={'pk': get_obj(s).pk}))),
            ('projecttype import', lambda s, c: c.post(reverse('projecttype-import'), data={'file': export_archive(get_obj(s))}, format='multipart')),
        ])
    if list:
        out.extend([
            ('projecttype get-predefined-finding-fields', lambda s, c: c.get(reverse('projecttype-get-predefined-finding-fields'))),
        ])
    return out


def expect_result(urls, allowed_users=None):
    all_users = {'public', 'guest', 'regular', 'template_editor', 'designer', 'user_manager', 'superuser'}

    for user in allowed_users or []:
        yield from [(user, *u, True) for u in urls]
    for user in all_users - set(allowed_users):
        yield from [(user, *u, False) for u in urls]



def public_urls():
    return [
        ('utils healthcheck', lambda s, c: c.get(reverse('utils-healthcheck'))),
    ]


def guest_urls():
    return [
        ('utils list', lambda s, c: c.get(reverse('utils-list'))),
        ('utils settings', lambda s, c: c.get(reverse('utils-settings'))),

        *viewset_urls('pentestuser', get_kwargs=lambda s, detail: {'pk': 'self'}, retrieve=True, update=True, update_partial=True),
        *viewset_urls('pentestuser', get_kwargs=lambda s, detail: {}, list=True),
        *viewset_urls('mfamethod', get_kwargs=lambda s, detail: {'pentestuser_pk': 'self'} | ({'pk': s.current_user.mfa_methods.get(is_primary=True).id if s.current_user else 'fake-uuid'} if detail else {}), list=True, retrieve=True, update=True, update_partial=True, destroy=True),
        ('mfamethod register backup', lambda s, c: c.post(reverse('mfamethod-register-backup-begin', kwargs={'pentestuser_pk': 'self'}))),
        ('mfamethod totp backup', lambda s, c: c.post(reverse('mfamethod-register-totp-begin', kwargs={'pentestuser_pk': 'self'}))),
        ('mfamethod fido2 backup', lambda s, c: c.post(reverse('mfamethod-register-fido2-begin', kwargs={'pentestuser_pk': 'self'}))),

        *viewset_urls('findingtemplate', get_kwargs=lambda s, detail: {'pk': s.template.pk} if detail else {}, list=True, retrieve=True),
        ('findingtemplate fielddefinition', lambda s, c: c.get(reverse('findingtemplate-fielddefinition'))),

        *projecttype_viewset_urls(get_obj=lambda s: s.project_type, list=True, read=True),
        *projecttype_viewset_urls(get_obj=lambda s: s.project_type_customized, read=True, write=True),

        *project_viewset_urls(get_obj=lambda s: s.project, list=True, read=True, write=True, destory=False, update=False),
        *project_viewset_urls(get_obj=lambda s: s.project_readonly, read=True),
    ]


def regular_user_urls():
    return [
        *viewset_urls('pentestuser', get_kwargs=lambda s, detail: {'pk': s.user_other.pk} if detail else {}, retrieve=True),

        *project_viewset_urls(get_obj=lambda s: s.project, create=True, update=True, destory=True),
        ('pentestproject readonly', lambda s, c: c.put(reverse('pentestproject-readonly', kwargs={'pk': s.project.pk}), data={'readonly': True})),
        ('pentestproject readonly', lambda s, c: c.put(reverse('pentestproject-readonly', kwargs={'pk': s.project_readonly.pk}), data={'readonly': False})),
    ]


def template_editor_urls():
    return {
        *viewset_urls('findingtemplate', get_kwargs=lambda s, detail: {'pk': s.template.pk} if detail else {}, create=True, update=True, update_partial=True, destroy=True, lock=True, unlock=True),
        ('findingtemplate export', lambda s, c: c.post(reverse('findingtemplate-export', kwargs={'pk': s.template.pk}))),
        ('findingtemplate import', lambda s, c: c.post(reverse('findingtemplate-import'), data={'file': export_archive(s.template)}, format='multipart')),
    }
    

def designer_urls():
    return [
        *projecttype_viewset_urls(get_obj=lambda s: s.project_type, create=True, write=True),
    ]


def user_manager_urls():
    return [
        *viewset_urls('pentestuser', get_kwargs=lambda s, detail: {'pk': s.user_other.pk} if detail else {}, create=True, create_data={'username': 'other', 'password': 'D40C4dEyH9Naam6!'}, update=True, update_partial=True),
        ('pentestuser reset-password', lambda s, c: c.post(reverse('pentestuser-reset-password', kwargs={'pk': s.user_other.pk}), data={'password': 'D40C4dEyH9Naam6!'})),
        *viewset_urls('mfamethod', get_kwargs=lambda s, detail: {'pentestuser_pk': s.user_other.pk} | ({'pk': s.user_other.mfa_methods.get(is_primary=True).pk} if detail else {}), list=True, retrieve=True, destroy=True),
    ]


def superuser_urls():
    return [
        # Not a project member
        *project_viewset_urls(get_obj=lambda s: s.project_unauthorized, read=True, write=True),
        *projecttype_viewset_urls(get_obj=lambda s: s.project_type_customized_unauthorized, read=True, write=True),

    ]
    

def forbidden_urls():
    return [
        *project_viewset_urls(get_obj=lambda s: s.project_readonly, write=True),
        ('mfamethod register backup', lambda s, c: c.post(reverse('mfamethod-register-backup-begin', kwargs={'pentestuser_pk': s.user_other.pk}))),
        ('mfamethod totp backup', lambda s, c: c.post(reverse('mfamethod-register-totp-begin', kwargs={'pentestuser_pk': s.user_other.pk}))),
        ('mfamethod fido2 backup', lambda s, c: c.post(reverse('mfamethod-register-fido2-begin', kwargs={'pentestuser_pk': s.user_other.pk}))),
    ]


def build_test_parameters():
    yield from expect_result(
        urls=public_urls(),
        allowed_users=['public', 'guest', 'regular', 'template_editor', 'designer', 'user_manager', 'superuser']
    )
    yield from expect_result(
        urls=guest_urls(),
        allowed_users=['guest', 'regular', 'template_editor', 'designer', 'user_manager', 'superuser']
    )
    yield from expect_result(
        urls=regular_user_urls(), 
        allowed_users=['regular', 'template_editor', 'designer', 'user_manager', 'superuser'],
    )
    yield from expect_result(
        urls=template_editor_urls(), 
        allowed_users=['template_editor', 'superuser'], 
    )
    yield from expect_result(
        urls=designer_urls(), 
        allowed_users=['designer', 'superuser'], 
    )
    yield from expect_result(
        urls=user_manager_urls(), 
        allowed_users=['user_manager', 'superuser'], 
    )
    yield from expect_result(
        urls=superuser_urls(), 
        allowed_users=['superuser'], 
    )
    yield from expect_result(
        urls=forbidden_urls(),
        allowed_users=[],
    )


@pytest.mark.django_db
class TestApiRequestsAndPermissions:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user_guest = create_user(username='guest', is_guest=True, mfa=True)
        self.user_regular = create_user(username='regular', mfa=True)
        self.user_template_editor = create_user(username='template_editor', is_template_editor=True, mfa=True)
        self.user_designer = create_user(username='designer', is_designer=True, mfa=True)
        self.user_user_manager = create_user(username='user_manager', is_user_manager=True, mfa=True)
        self.user_superuser = create_user(username='superuser', is_superuser=True, is_staff=True, mfa=True)
        self.user_map = {
            'guest': self.user_guest,
            'regular': self.user_regular,
            'template_editor': self.user_template_editor,
            'designer': self.user_designer,
            'user_manager': self.user_user_manager,
            'superuser': self.user_superuser,
        }

        self.user_other = create_user(mfa=True)
        self.current_user = None
    
        self.project = create_project(members=self.user_map.values())
        self.project_readonly = create_project(members=self.user_map.values(), readonly=True)
        self.project_unauthorized = create_project()

        self.project_type = create_project_type()
        self.project_type_customized = create_project_type(source=SourceEnum.CUSTOMIZED, linked_project=self.project)
        self.project_type_customized_unauthorized = create_project_type(source=SourceEnum.CUSTOMIZED, linked_project=self.project_unauthorized)

        self.template = create_template()

        with override_settings(
                GUEST_USERS_CAN_IMPORT_PROJECTS=False,
                GUEST_USERS_CAN_CREATE_PROJECTS=False,
                GUEST_USERS_CAN_DELETE_PROJECTS=False,
                GUEST_USERS_CAN_UPDATE_PROJECT_SETTINGS=False,
            ):
            yield

    @pytest.mark.parametrize('user,name,perform_request,expected', sorted(build_test_parameters(), key=lambda t: (t[0], t[1], t[3])))
    def test_api_requests(self, user, name, perform_request, expected):
        client = APIClient()
        if user_obj := self.user_map.get(user):
            client.force_authenticate(user_obj)
            session = client.session
            session['authentication_info'] = {
                'login_time': timezone.now().isoformat(),
                'reauth_time': timezone.now().isoformat(),
            }
            session.save()
            assert 'authentication_info' in dict(client.session)
            self.current_user = user_obj

        res = perform_request(self, client)
        info = res.data if not isinstance(res, (FileResponse, StreamingHttpResponse)) else res
        if expected:
            assert 200 <= res.status_code < 300, {'message': 'API request failed, but should have succeeded', 'info': info}
        else:
            assert 400 <= res.status_code < 500, {'message': 'API request succeeded, but should have failed', 'info': info}

