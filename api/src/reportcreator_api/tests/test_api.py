from datetime import timedelta
from functools import cached_property
from typing import Optional
from uuid import uuid4

import pytest
from django.core.files.base import ContentFile
from django.http import FileResponse, StreamingHttpResponse
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from reportcreator_api.archive.import_export import export_project_types, export_projects, export_templates
from reportcreator_api.archive.import_export.import_export import export_notes
from reportcreator_api.notifications.models import NotificationSpec, UserNotification
from reportcreator_api.pentests.models import (
    FindingTemplate,
    Language,
    PentestProject,
    ProjectType,
    ProjectTypeScope,
    SourceEnum,
    UploadedUserNotebookFile,
    UploadedUserNotebookImage,
)
from reportcreator_api.tests.mock import (
    create_archived_project,
    create_png_file,
    create_project,
    create_project_type,
    create_template,
    create_user,
)
from reportcreator_api.users.models import AuthIdentity, PentestUser


def export_archive(obj):
    if isinstance(obj, ProjectType):
        exp = export_project_types([obj])
    elif isinstance(obj, FindingTemplate):
        exp = export_templates([obj])
    elif isinstance(obj, PentestProject):
        exp = export_projects([obj])
    return ContentFile(content=b''.join(exp), name='export.tar.gz')


def export_notes_archive(obj):
    return ContentFile(content=b''.join(export_notes(obj)) if obj else b'', name='export.tar.gz')


def viewset_urls(basename, get_kwargs, create_data=None, list=False, retrieve=False, create=False, update=False, update_partial=False, destroy=False, lock=False, unlock=False, history_timeline=False):
    list_urlname = basename + '-list'
    detail_urlname = basename + '-detail'

    out = []
    if list:
        out.append((basename + ' list', lambda s, c: c.get(reverse(list_urlname, kwargs=get_kwargs(s, False))), lambda s: get_kwargs(s, True)))
    if retrieve:
        out.append((basename + ' retrieve', lambda s, c: c.get(reverse(detail_urlname, kwargs=get_kwargs(s, True)))))
    if create:
        out.append((basename + ' create', lambda s, c: c.post(reverse(list_urlname, kwargs=get_kwargs(s, False)), data=c.get(reverse(detail_urlname, kwargs=get_kwargs(s, True))).data | (create_data or {}))))
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
    if history_timeline:
        out.append((basename + ' history-timeline', lambda s, c: c.get(reverse(basename + '-history-timeline', kwargs=get_kwargs(s, True)))))
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
                format='multipart',
            )),
        ])
    return out


def project_viewset_urls(get_obj, read=False, write=False, create=False, list=False, destory=None, update=None):
    destory = destory if destory is not None else write
    update = update if update is not None else write

    out = [
        *viewset_urls('pentestproject', get_kwargs=lambda s, detail: {'pk': get_obj(s).pk} if detail else {}, list=list, retrieve=read, create=create, update=update, update_partial=update, destroy=destory, history_timeline=read),
        *viewset_urls('section', get_kwargs=lambda s, detail: {'project_pk': get_obj(s).pk} | ({'id': get_obj(s).sections.first().section_id} if detail else {}), list=read, retrieve=read, update=write, update_partial=write, history_timeline=read),
        *viewset_urls('finding', get_kwargs=lambda s, detail: {'project_pk': get_obj(s).pk} | ({'id': get_obj(s).findings.first().finding_id} if detail else {}), list=read, retrieve=read, create=write, destroy=write, update=write, update_partial=write, history_timeline=read),
        *viewset_urls('projectnotebookpage', get_kwargs=lambda s, detail: {'project_pk': get_obj(s).pk} | ({'id': get_obj(s).notes.first().note_id} if detail else {}), list=read, retrieve=read, create=write, destroy=write, update=write, update_partial=write, history_timeline=read),
        *file_viewset_urls('uploadedimage', get_base_kwargs=lambda s: {'project_pk': get_obj(s).pk}, get_obj=lambda s: get_obj(s).images.first(), read=read, write=write),
        *file_viewset_urls('uploadedprojectfile', get_base_kwargs=lambda s: {'project_pk': get_obj(s).pk}, get_obj=lambda s: get_obj(s).files.first(), read=read, write=write),
    ]
    if read:
      out.extend([
            ('pentestproject check', lambda s, c: c.get(reverse('pentestproject-check', kwargs={'pk': get_obj(s).pk}))),
            ('pentestproject export', lambda s, c: c.post(reverse('pentestproject-export', kwargs={'pk': get_obj(s).pk}))),
            ('pentestproject export-all', lambda s, c: c.post(reverse('pentestproject-export-all', kwargs={'pk': get_obj(s).pk}))),
            ('pentestproject preview', lambda s, c: c.post(reverse('pentestproject-preview', kwargs={'pk': get_obj(s).pk}), data={})),
            ('pentestproject generate', lambda s, c: c.post(reverse('pentestproject-generate', kwargs={'pk': get_obj(s).pk}), data={'password': 'pdf-password'})),
            ('pentestproject md2html', lambda s, c: c.post(reverse('pentestproject-md2html', kwargs={'pk': get_obj(s).pk}), data={})),
            ('projectnotebookpage export', lambda s, c: c.post(reverse('projectnotebookpage-export', kwargs={'project_pk': get_obj(s).pk, 'id': get_obj(s).notes.first().note_id}))),
            ('projectnotebookpage export-all', lambda s, c: c.post(reverse('projectnotebookpage-export-all', kwargs={'project_pk': get_obj(s).pk}))),
            ('projectnotebookpage export-pdf', lambda s, c: c.post(reverse('projectnotebookpage-export-pdf', kwargs={'project_pk': get_obj(s).pk, 'id': get_obj(s).notes.first().note_id}))),

            ('pentestprojecthistory project', lambda s, c: c.get(reverse('pentestprojecthistory-detail', kwargs={'project_pk': get_obj(s).pk, 'history_date': s.history_date}))),
            ('pentestprojecthistory section', lambda s, c: c.get(reverse('pentestprojecthistory-section', kwargs={'project_pk': get_obj(s).pk, 'id': get_obj(s).sections.first().section_id, 'history_date': s.history_date}))),
            ('pentestprojecthistory section', lambda s, c: c.get(reverse('pentestprojecthistory-finding', kwargs={'project_pk': get_obj(s).pk, 'id': get_obj(s).findings.first().finding_id, 'history_date': s.history_date}))),
            ('pentestprojecthistory section', lambda s, c: c.get(reverse('pentestprojecthistory-note', kwargs={'project_pk': get_obj(s).pk, 'id': get_obj(s).notes.first().note_id, 'history_date': s.history_date}))),
            ('pentestprojecthistory image-by-name', lambda s, c: c.get(reverse('pentestprojecthistory-image-by-name', kwargs={'project_pk': get_obj(s).pk, 'filename': get_obj(s).images.first().name, 'history_date': s.history_date}))),
            ('pentestprojecthistory file-by-name', lambda s, c: c.get(reverse('pentestprojecthistory-file-by-name', kwargs={'project_pk': get_obj(s).pk, 'filename': get_obj(s).files.first().name, 'history_date': s.history_date}))),
        ])
    if write:
        out.extend([
            ('pentestproject finding-fromtemplate', lambda s, c: c.post(reverse('finding-fromtemplate', kwargs={'project_pk': get_obj(s).pk}), data={'template': s.template.pk})),
            ('finding sort', lambda s, c: c.post(reverse('finding-sort', kwargs={'project_pk': get_obj(s).pk}), data=[{'id': get_obj(s).findings.first().finding_id, 'order': 1}])),
            ('projectnotebookpage sort', lambda s, c: c.post(reverse('projectnotebookpage-sort', kwargs={'project_pk': get_obj(s).pk}), data=[{'id': get_obj(s).notes.first().note_id, 'parent': None, 'order': 1}])),
            ('projectnotebookpage import', lambda s, c: c.post(reverse('projectnotebookpage-import', kwargs={'project_pk': get_obj(s).pk}), data={'file': export_notes_archive(get_obj(s))}, format='multipart')),
            ('pentestproject upload-image-or-file', lambda s, c: c.post(reverse('pentestproject-upload-image-or-file', kwargs={'pk': get_obj(s).pk}), data={'name': 'image.png', 'file': ContentFile(name='image.png', content=create_png_file())}, format='multipart')),
            ('pentestproject upload-image-or-file', lambda s, c: c.post(reverse('pentestproject-upload-image-or-file', kwargs={'pk': get_obj(s).pk}), data={'name': 'test.pdf', 'file': ContentFile(name='text.pdf', content=b'text')}, format='multipart')),
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


def projecttype_viewset_urls(get_obj, read=False, write=False, create_global=False, list=False):
    out = [
        *viewset_urls('projecttype', get_kwargs=lambda s, detail: {'pk': get_obj(s).pk} if detail else {}, list=list, retrieve=read, create=create_global, create_data={'scope': ProjectTypeScope.GLOBAL}, update=write, update_partial=write, destroy=write, lock=write, unlock=write, history_timeline=read),
        *file_viewset_urls('uploadedasset', get_base_kwargs=lambda s: {'projecttype_pk': get_obj(s).pk}, get_obj=lambda s: get_obj(s).assets.first(), read=read, write=write),
    ]
    if read:
        out.extend([
            ('projecttype preview', lambda s, c: c.post(reverse('projecttype-preview', kwargs={'pk': get_obj(s).pk}), data={'report_template': '', 'report_styles': '', 'report_preview_data': {}})),
            ('projecttype export', lambda s, c: c.post(reverse('projecttype-export', kwargs={'pk': get_obj(s).pk}))),
            ('projecttype copy private', lambda s, c: c.post(reverse('projecttype-copy', kwargs={'pk': get_obj(s).pk}), data={'scope': ProjectTypeScope.PRIVATE})),
            ('projecttypehistory detail', lambda s, c: c.get(reverse('projecttypehistory-detail', kwargs={'projecttype_pk': get_obj(s).pk, 'history_date': s.history_date}))),
            ('projecttypehistory asset-by-name', lambda s, c: c.get(reverse('projecttypehistory-asset-by-name', kwargs={'projecttype_pk': get_obj(s).pk, 'filename': get_obj(s).assets.first().name, 'history_date': s.history_date}))),
        ])
    if create_global:
        out.extend([
            ('projecttype import global', lambda s, c: c.post(reverse('projecttype-import'), data={'file': export_archive(get_obj(s)), 'scope': ProjectTypeScope.GLOBAL}, format='multipart')),
            ('projecttype copy global', lambda s, c: c.post(reverse('projecttype-copy', kwargs={'pk': get_obj(s).pk}), data={'scope': ProjectTypeScope.GLOBAL})),
        ])
    if list:
        out.extend([
            ('projecttype get-predefined-finding-fields', lambda s, c: c.get(reverse('projecttype-get-predefined-finding-fields'))),
        ])
    return out


def expect_result(urls, allowed_users=None):
    all_users = {'public', 'guest', 'regular', 'template_editor', 'designer', 'user_manager', 'superuser'}
    urls = [((*u, None) if len(u) == 2 else u) for u in urls]

    for user in allowed_users or []:
        yield from [(user, *u, True) for u in urls]
    for user in all_users - set(allowed_users or []):
        yield from [(user, *u, False) for u in urls]



def public_urls():
    return [
        ('utils healthcheck', lambda s, c: c.get(reverse('utils-healthcheck'))),
        ('utils settings', lambda s, c: c.get(reverse('utils-settings'))),
        ('utils openapi', lambda s, c: c.get(reverse('utils-openapi-schema'))),
    ]


def guest_urls():
    return [
        ('utils list', lambda s, c: c.get(reverse('utils-list'))),
        ('utils cwes', lambda s, c: c.get(reverse('utils-cwes'))),

        *viewset_urls('pentestuser', get_kwargs=lambda s, detail: {'pk': 'self'}, retrieve=True, update=True, update_partial=True),
        *viewset_urls('pentestuser', get_kwargs=lambda s, detail: {}, list=True),
        *viewset_urls('mfamethod', get_kwargs=lambda s, detail: {'pentestuser_pk': 'self'} | ({'pk': s.current_user.mfa_methods.get(is_primary=True).id if s.current_user else uuid4()} if detail else {}), list=True, retrieve=True, update=True, update_partial=True, destroy=True),
        ('mfamethod register backup', lambda s, c: c.post(reverse('mfamethod-register-backup-begin', kwargs={'pentestuser_pk': 'self'}))),
        ('mfamethod totp backup', lambda s, c: c.post(reverse('mfamethod-register-totp-begin', kwargs={'pentestuser_pk': 'self'}))),
        ('mfamethod fido2 backup', lambda s, c: c.post(reverse('mfamethod-register-fido2-begin', kwargs={'pentestuser_pk': 'self'}))),
        *viewset_urls('notification', get_kwargs=lambda s, detail: {'pentestuser_pk': 'self'} | ({'pk': s.notification.id if s.current_user else uuid4()} if detail else {}), list=True, retrieve=True, update=True, update_partial=True),
        *viewset_urls('userpublickey', get_kwargs=lambda s, detail: {'pentestuser_pk': 'self'} | ({'pk': s.current_user.public_keys.first().id if s.current_user else uuid4()} if detail else {}), list=True, retrieve=True, update=True, update_partial=True),
        *viewset_urls('apitoken', get_kwargs=lambda s, detail: {'pentestuser_pk': 'self'} | ({'pk': s.current_user.api_tokens.first().pk if s.current_user else uuid4()} if detail else {}), create=True, list=True, retrieve=True, destroy=True),

        *viewset_urls('usernotebookpage', get_kwargs=lambda s, detail: {'pentestuser_pk': 'self'} | ({'id': s.current_user.notes.first().note_id if s.current_user else uuid4()} if detail else {}), list=True, retrieve=True, create=True, update=True, update_partial=True, destroy=True),
        ('usernotebookpage sort', lambda s, c: c.post(reverse('usernotebookpage-sort', kwargs={'pentestuser_pk': 'self'}), data=[])),
        *file_viewset_urls('uploadedusernotebookimage', get_obj=lambda s: s.current_user.images.first() if s.current_user else UploadedUserNotebookImage(name='nonexistent.png'), get_base_kwargs=lambda s: {'pentestuser_pk': 'self'}, read=True, write=True),
        *file_viewset_urls('uploadedusernotebookfile', get_obj=lambda s: s.current_user.files.first() if s.current_user else UploadedUserNotebookFile(name='nonexistent.pdf'), get_base_kwargs=lambda s: {'pentestuser_pk': 'self'}, read=True, write=True),
        ('usernotebookpage upload-image-or-file', lambda s, c: c.post(reverse('usernotebookpage-upload-image-or-file', kwargs={'pentestuser_pk': 'self'}), data={'name': 'image.png', 'file': ContentFile(name='image.png', content=create_png_file())}, format='multipart')),
        ('usernotebookpage upload-image-or-file', lambda s, c: c.post(reverse('usernotebookpage-upload-image-or-file', kwargs={'pentestuser_pk': 'self'}), data={'name': 'test.pdf', 'file': ContentFile(name='text.pdf', content=b'text')}, format='multipart')),
        ('usernotebookoage export', lambda s, c: c.post(reverse('usernotebookpage-export', kwargs={'pentestuser_pk': 'self', 'id': s.current_user.notes.first().note_id if s.current_user else uuid4()}))),
        ('usernotebookoage export-all', lambda s, c: c.post(reverse('usernotebookpage-export-all', kwargs={'pentestuser_pk': 'self'}))),
        ('usernotebookpage export-pdf', lambda s, c: c.post(reverse('usernotebookpage-export-pdf', kwargs={'pentestuser_pk': 'self', 'id': s.current_user.notes.first().note_id if s.current_user else uuid4()}))),
        ('usernotebookpage import', lambda s, c: c.post(reverse('usernotebookpage-import', kwargs={'pentestuser_pk': 'self'}), data={'file': export_notes_archive(s.current_user)}, format='multipart')),

        *viewset_urls('findingtemplate', get_kwargs=lambda s, detail: {'pk': s.template.pk} if detail else {}, list=True, retrieve=True),
        *viewset_urls('findingtemplatetranslation', get_kwargs=lambda s, detail: {'template_pk': s.template.pk} | ({'pk': s.template.main_translation.pk} if detail else {}), list=True, retrieve=True, history_timeline=True),
        *file_viewset_urls('uploadedtemplateimage', get_obj=lambda s: s.template.images.first(), get_base_kwargs=lambda s: {'template_pk': s.template.pk}, read=True),
        ('findingtemplate fielddefinition', lambda s, c: c.get(reverse('findingtemplate-fielddefinition')), lambda s: [s.template, s.project_type]),
        ('findingtemplatehistory template', lambda s, c: c.get(reverse('findingtemplatehistory-detail', kwargs={'template_pk': s.template.pk, 'history_date': s.history_date}))),
        ('findingtemplatehistory image-by-name', lambda s, c: c.get(reverse('findingtemplatehistory-image-by-name', kwargs={'template_pk': s.template.pk, 'filename': s.template.images.first().name, 'history_date': s.history_date}))),

        ('projecttype create private', lambda s, c: c.post(reverse('projecttype-list'), data=c.get(reverse('projecttype-detail', kwargs={'pk': s.project_type.pk})).data | {'scope': ProjectTypeScope.PRIVATE})),
        ('projecttype import private', lambda s, c: c.post(reverse('projecttype-import'), data={'file': export_archive(s.project_type), 'scope': ProjectTypeScope.PRIVATE}, format='multipart')),
        *projecttype_viewset_urls(get_obj=lambda s: s.project_type, list=True, read=True),
        *projecttype_viewset_urls(get_obj=lambda s: s.project_type_customized, read=True, write=True),
        *projecttype_viewset_urls(get_obj=lambda s: s.project_type_snapshot, read=True),
        *projecttype_viewset_urls(get_obj=lambda s: s.project_type_private, read=True, write=True),

        *project_viewset_urls(get_obj=lambda s: s.project, list=True, read=True, write=True, destory=False, update=False),
        *project_viewset_urls(get_obj=lambda s: s.project_readonly, read=True),

        *viewset_urls('archivedproject', get_kwargs=lambda s, detail: {'pk': s.archived_project.pk} if detail else {}, list=True, retrieve=True),
        *viewset_urls('archivedprojectkeypart', get_kwargs=lambda s, detail: {'archivedproject_pk': s.archived_project.pk} | ({'pk': s.archived_project.key_parts.first().pk} if detail else {}), list=True, retrieve=True),
        ('archivedprojectkeypart public-key-encrypted-data', lambda s, c: c.get(reverse('archivedprojectkeypart-public-key-encrypted-data', kwargs={'archivedproject_pk': s.archived_project.pk, 'pk': getattr(s.archived_project.key_parts.filter(user=s.current_user).first(), 'pk', uuid4())}))),
    ]


def regular_user_urls():
    return [
        *viewset_urls('pentestuser', get_kwargs=lambda s, detail: {'pk': s.user_other.pk} if detail else {}, retrieve=True),

        *project_viewset_urls(get_obj=lambda s: s.project, create=True, update=True, destory=True),
        ('pentestproject readonly', lambda s, c: c.put(reverse('pentestproject-readonly', kwargs={'pk': s.project.pk}), data={'readonly': True})),
        *project_viewset_urls(get_obj=lambda s: s.project_readonly, destory=True),
        ('pentestproject readonly', lambda s, c: c.put(reverse('pentestproject-readonly', kwargs={'pk': s.project_readonly.pk}), data={'readonly': False})),

        ('pentestproject archive-check', lambda s, c: c.get(reverse('pentestproject-archive-check', kwargs={'pk': s.project_readonly.pk}))),
        ('pentestproject archive', lambda s, c: c.post(reverse('pentestproject-archive', kwargs={'pk': s.project_readonly.pk}))),
    ]


def template_editor_urls():
    return {
        *viewset_urls('findingtemplate', get_kwargs=lambda s, detail: {'pk': s.template.pk} if detail else {}, create=True, update=True, update_partial=True, destroy=True, lock=True, unlock=True),
        *viewset_urls('findingtemplatetranslation', get_kwargs=lambda s, detail: {'template_pk': s.template.pk} | ({'pk': s.template.main_translation.pk} if detail else {}), create=True, create_data={'language': Language.GERMAN_DE, 'data': {'title': 'test'}}, update=True, update_partial=True),
        *file_viewset_urls('uploadedtemplateimage', get_obj=lambda s: s.template.images.first(), get_base_kwargs=lambda s: {'template_pk': s.template.pk}, write=True),
        ('findingtemplate copy', lambda s, c: c.post(reverse('findingtemplate-copy', kwargs={'pk': s.template.pk}), data={})),
        ('findingtemplate export', lambda s, c: c.post(reverse('findingtemplate-export', kwargs={'pk': s.template.pk}))),
        ('findingtemplate import', lambda s, c: c.post(reverse('findingtemplate-import'), data={'file': export_archive(s.template)}, format='multipart')),
        ('findingtemplate fromfinding', lambda s, c: c.post(reverse('findingtemplate-fromfinding'), data={'project': s.project.id, 'translations': [{'is_main': True, 'data': {'title': 'title'}}]})),
    }


def designer_urls():
    return [
        *projecttype_viewset_urls(get_obj=lambda s: s.project_type, create_global=True, write=True),
    ]


def user_manager_urls():
    return [
        *viewset_urls('pentestuser', get_kwargs=lambda s, detail: {'pk': s.user_other.pk} if detail else {}, create=True, create_data={'username': 'new', 'password': 'D40C4dEyH9Naam6!'}, update=True, update_partial=True),
        ('pentestuser reset-password', lambda s, c: c.post(reverse('pentestuser-reset-password', kwargs={'pk': s.user_other.pk}), data={'password': 'D40C4dEyH9Naam6!'})),
        *viewset_urls('mfamethod', get_kwargs=lambda s, detail: {'pentestuser_pk': s.user_other.pk} | ({'pk': s.user_other.mfa_methods.get(is_primary=True).pk} if detail else {}), list=True, retrieve=True, destroy=True),
        *viewset_urls('authidentity', get_kwargs=lambda s, detail: {'pentestuser_pk': s.user_other.pk} | ({'pk': s.user_other.auth_identities.first().pk} if detail else {}), list=True, retrieve=True, create=True, create_data={'identifier': 'other.identifier'}, update=True, update_partial=True, destroy=True),
        *viewset_urls('apitoken', get_kwargs=lambda s, detail: {'pentestuser_pk': s.user_other.pk} | ({'pk': s.user_other.api_tokens.first().pk} if detail else {}), list=True, retrieve=True, destroy=True),
        *viewset_urls('userpublickey', get_kwargs=lambda s, detail: {'pentestuser_pk': s.user_other.pk} | ({'pk': s.user_other.public_keys.first().pk} if detail else {}), list=True, retrieve=True),
        ('utils-license', lambda s, c: c.get(reverse('utils-license'))),
    ]


def superuser_urls():
    return [
        ('pentestuser enable-admin-permissions', lambda s, c: c.post(reverse('pentestuser-enable-admin-permissions'))),
        ('pentestuser disable-admin-permissions', lambda s, c: c.post(reverse('pentestuser-disable-admin-permissions'))),

        *projecttype_viewset_urls(get_obj=lambda s: s.project_type_snapshot, write=True),

        # Not a project member
        *project_viewset_urls(get_obj=lambda s: s.project_unauthorized, read=True, write=True),
        *projecttype_viewset_urls(get_obj=lambda s: s.project_type_customized_unauthorized, read=True, write=True),
        *projecttype_viewset_urls(get_obj=lambda s: s.project_type_private_unauthorized, read=True, write=True),

        ('pentestproject archive-check', lambda s, c: c.get(reverse('pentestproject-archive-check', kwargs={'pk': s.project_readonly_unauthorized.pk}))),
        ('pentestproject archive', lambda s, c: c.post(reverse('pentestproject-archive', kwargs={'pk': s.project_readonly_unauthorized.pk}))),
        *viewset_urls('archivedproject', get_kwargs=lambda s, detail: {'pk': s.archived_project_unauthorized.pk} if detail else {}, retrieve=True),
        *viewset_urls('archivedprojectkeypart', get_kwargs=lambda s, detail: {'archivedproject_pk': s.archived_project_unauthorized.pk} | ({'pk': s.archived_project_unauthorized.key_parts.first().pk} if detail else {}), list=True, retrieve=True),
        ('archivedprojectkeypart public-key-encrypted-data', lambda s, c: c.get(reverse('archivedprojectkeypart-public-key-encrypted-data', kwargs={'archivedproject_pk': s.archived_project_unauthorized.pk, 'pk': s.archived_project_unauthorized.key_parts.first().pk}))),
    ]


def forbidden_urls():
    return [
        *project_viewset_urls(get_obj=lambda s: s.project_readonly, write=True, destory=False),
        ('mfamethod register backup', lambda s, c: c.post(reverse('mfamethod-register-backup-begin', kwargs={'pentestuser_pk': s.user_other.pk}))),
        ('mfamethod totp backup', lambda s, c: c.post(reverse('mfamethod-register-totp-begin', kwargs={'pentestuser_pk': s.user_other.pk}))),
        ('mfamethod fido2 backup', lambda s, c: c.post(reverse('mfamethod-register-fido2-begin', kwargs={'pentestuser_pk': s.user_other.pk}))),
        *viewset_urls('mfamethod', get_kwargs=lambda s, detail: {'pentestuser_pk': s.user_other.pk} | ({'pk': s.user_other.mfa_methods.get(is_primary=True).pk} if detail else {}), create=True, update=True, update_partial=True),
        *viewset_urls('apitoken', get_kwargs=lambda s, detail: {'pentestuser_pk': s.user_other.pk} | ({'pk': s.user_other.api_tokens.first().pk} if detail else {}), create=True),
        *viewset_urls('userpublickey', get_kwargs=lambda s, detail: {'pentestuser_pk': s.user_other.pk} | ({'pk': s.user_other.public_keys.first().pk} if detail else {}), create=True, update=True, update_partial=True, destroy=True),
        ('userpublickey register begin', lambda s, c: c.post(reverse('userpublickey-register-begin', kwargs={'pentestuser_pk': s.user_other.pk}), data={'name': 'new', 'public_key': s.user_other.public_keys.first().public_key})),
    ]


def build_test_parameters():
    yield from expect_result(
        urls=public_urls(),
        allowed_users=['public', 'guest', 'regular', 'template_editor', 'designer', 'user_manager', 'superuser'],
    )
    yield from expect_result(
        urls=guest_urls(),
        allowed_users=['guest', 'regular', 'template_editor', 'designer', 'user_manager', 'superuser'],
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


class ApiRequestsAndPermissionsTestData:
    def __init__(self, current_user: Optional[PentestUser]) -> None:
        self.current_user = current_user

    @classmethod
    def create_user(cls, is_superuser=False, **kwargs):
        return create_user(mfa=True, apitoken=True, public_key=True, is_superuser=is_superuser, **kwargs)

    @cached_property
    def user_other(self):
        user = self.create_user(username='other')
        AuthIdentity.objects.create(user=user, provider='dummy', identifier='other.user@example.com')
        return user

    @cached_property
    def notification(self):
        NotificationSpec.objects.create(text='Test')
        return self.current_user.notifications.first() if self.current_user else UserNotification()

    @cached_property
    def project(self):
        return create_project(members=[self.current_user] if self.current_user else [self.user_other])

    @cached_property
    def project_readonly(self):
        return create_project(members=[self.current_user] if self.current_user else [self.user_other], readonly=True)

    @cached_property
    def project_unauthorized(self):
        return create_project(members=[self.user_other])

    @cached_property
    def project_readonly_unauthorized(self):
        return create_project(members=[self.user_other], readonly=True)

    @cached_property
    def archived_project(self):
        return create_archived_project(self.project_readonly)

    @cached_property
    def archived_project_unauthorized(self):
        return create_archived_project(self.project_readonly_unauthorized)

    @cached_property
    def project_type(self):
        return create_project_type()

    @cached_property
    def project_type_customized(self):
        return create_project_type(source=SourceEnum.CUSTOMIZED, linked_project=self.project)

    @cached_property
    def project_type_customized_unauthorized(self):
        return create_project_type(source=SourceEnum.CUSTOMIZED, linked_project=self.project_unauthorized)

    @cached_property
    def project_type_snapshot(self):
        return create_project_type(source=SourceEnum.SNAPSHOT, linked_project=self.project)

    @cached_property
    def project_type_private(self):
        return create_project_type(source=SourceEnum.CREATED, linked_user=self.current_user)

    @cached_property
    def project_type_private_unauthorized(self):
        return create_project_type(source=SourceEnum.CREATED, linked_user=self.user_other)

    @cached_property
    def template(self):
        return create_template()

    @property
    def history_date(self):
        # Use a history date in the future to ensure it is always after the actual object is created and never before
        return (timezone.now() + timedelta(days=1)).isoformat()


@pytest.mark.django_db()
@pytest.mark.parametrize(('username', 'name', 'perform_request', 'initialize_dependencies', 'expected'), sorted(build_test_parameters(), key=lambda t: (t[0], t[1], t[4])))
def test_api_requests(username, name, perform_request, initialize_dependencies, expected):
    with override_settings(
            GUEST_USERS_CAN_IMPORT_PROJECTS=False,
            GUEST_USERS_CAN_CREATE_PROJECTS=False,
            GUEST_USERS_CAN_DELETE_PROJECTS=False,
            GUEST_USERS_CAN_UPDATE_PROJECT_SETTINGS=False,
            ARCHIVING_THRESHOLD=1,
            AUTHLIB_OAUTH_CLIENTS={
                'dummy': {
                    'label': 'Dummy',
                },
            },
        ):
        user_map = {
            'public': lambda: None,
            'guest': lambda: ApiRequestsAndPermissionsTestData.create_user(is_guest=True),
            'regular': lambda: ApiRequestsAndPermissionsTestData.create_user(),
            'template_editor': lambda: ApiRequestsAndPermissionsTestData.create_user(is_template_editor=True),
            'designer': lambda: ApiRequestsAndPermissionsTestData.create_user(is_designer=True),
            'user_manager': lambda: ApiRequestsAndPermissionsTestData.create_user(is_user_manager=True),
            'superuser': lambda: ApiRequestsAndPermissionsTestData.create_user(is_superuser=True),
        }
        user = user_map[username]()
        data = ApiRequestsAndPermissionsTestData(user)
        client = APIClient()
        if user:
            if user.is_superuser:
                user.admin_permissions_enabled = True
            client.force_authenticate(user)
            session = client.session
            session['authentication_info'] = {
                'login_time': timezone.now().isoformat(),
                'reauth_time': timezone.now().isoformat(),
            }
            session.save()

        if initialize_dependencies:
            initialize_dependencies(data)
        res = perform_request(data, client)
        info = res.data if not isinstance(res, (FileResponse, StreamingHttpResponse)) else res
        if expected:
            assert 200 <= res.status_code < 300, {'message': 'API request failed, but should have succeeded', 'info': info}
        else:
            assert 400 <= res.status_code < 500, {'message': 'API request succeeded, but should have failed', 'info': info}
