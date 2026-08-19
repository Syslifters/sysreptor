from datetime import timedelta
from uuid import uuid4

import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from sysreptor.pentests.models import (
    NoteType,
    ShareInfo,
    UploadedProjectFile,
    UploadedUserNotebookFile,
    UploadedUserNotebookImage,
)
from sysreptor.tests.mock import (
    api_client,
    create_png_file,
    create_project,
    create_projectnotebookpage,
    create_shareinfo,
    create_user,
    create_usernotebookpage,
    mock_time,
    update,
)
from sysreptor.tests.test_crypto import assert_db_field_encrypted
from sysreptor.utils import crypto

SECRET_FILE_CONTENT = b'TOP-SECRET: cross-note leak PoC token'
SECRET_IMAGE_CONTENT = create_png_file() + b'SECRET-IMAGE'


def response_body(res) -> bytes:
    if getattr(res, 'streaming_content', None) is not None:
        return b''.join(res.streaming_content)
    return res.content


@pytest.mark.django_db()
class TestSharedProjectNotePermissions:
    @pytest.fixture(autouse=True)
    @mock_time(before=timedelta(days=1))
    def setUp(self):
        self.project = create_project(
            notes_kwargs=[],
            findings_kwargs=[{'data': {'description': '![](/images/name/img3.png)\n[file](/files/name/file3.txt)'}}],
            images_kwargs=[{'name': f'img{i}.png'} for i in range(4)],
            files_kwargs=[{'name': f'file{i}.txt'} for i in range(4)],
        )
        self.client = api_client(user=None)

        self.note_shared = create_projectnotebookpage(project=self.project, text='![](/images/name/img0.png)\n[file](/files/name/file0.txt)')
        self.childnote_shared = create_projectnotebookpage(project=self.project, parent=self.note_shared, text='![](/images/name/img1.png)\n[file](/files/name/file1.txt)')
        self.share_info = create_shareinfo(projectnote=self.note_shared)

        self.note_not_shared = create_projectnotebookpage(project=self.project, text='![](/images/name/img2.png)\n[file](/files/name/file2.txt)')
        self.childnote_not_shared = create_projectnotebookpage(project=self.project, parent=self.note_not_shared)

    @pytest.mark.parametrize(('note', 'expected'), [
        ('note_shared', True),
        ('childnote_shared', True),
        ('note_not_shared', False),
        ('childnote_not_shared', False),
    ])
    def test_access(self, note, expected):
        note_id = getattr(self, note).note_id
        res = self.client.get(reverse('sharednote-detail', kwargs={'shareinfo_pk': self.share_info.id, 'id': note_id}))
        assert res.status_code == (200 if expected else 404), res.data

    @pytest.mark.parametrize(('parent', 'expected'), [
        ('note_shared', True),
        ('childnote_shared', True),
        ('note_not_shared', False),
        ('childnote_not_shared', False),
        (None, False),
    ])
    def test_create(self, parent, expected):
        parent_id = getattr(self, parent).note_id if parent else None
        data = self.client.get(reverse('sharednote-detail', kwargs={'shareinfo_pk': self.share_info.id, 'id': self.note_shared.note_id})).data
        res = self.client.post(reverse('sharednote-list', kwargs={'shareinfo_pk': self.share_info.id}), data=data | {
            'parent': parent_id,
        })
        assert res.status_code == (201 if expected else 400), res.data
        if expected:
            res_list = self.client.get(reverse('sharednote-list', kwargs={'shareinfo_pk': self.share_info.id}))
            assert res.data['id'] in [n['id'] for n in res_list.data]
            res_detail = self.client.get(reverse('sharednote-detail', kwargs={'shareinfo_pk': self.share_info.id, 'id': res.data['id']}))
            assert res_detail.status_code == 200

    @pytest.mark.parametrize(('note', 'expected'), [
        ('note_shared', False),
        ('childnote_shared', True),
        ('note_not_shared', False),
        ('childnote_not_shared', False),
    ])
    def test_delete(self, note, expected):
        note_id = getattr(self, note).note_id
        res = self.client.delete(reverse('sharednote-detail', kwargs={'shareinfo_pk': self.share_info.id, 'id': note_id}))
        assert res.status_code in ([204] if expected else [400, 404])

    def test_list_includes_only_childnotes(self):
        res = self.client.get(reverse('sharednote-list', kwargs={'shareinfo_pk': self.share_info.id}))
        assert set([n['id'] for n in res.data]) == {str(self.note_shared.note_id), str(self.childnote_shared.note_id)}

    def test_shared_childnote(self):
        update(self.note_shared, parent=self.note_not_shared)

        res = self.client.get(reverse('sharednote-list', kwargs={'shareinfo_pk': self.share_info.id}))
        assert set([n['id'] for n in res.data]) == {str(self.note_shared.note_id), str(self.childnote_shared.note_id)}

    @pytest.mark.parametrize(('filename', 'expected'), [
        ('img0.png', True),
        ('img1.png', True),
        ('img2.png', False),
        ('img3.png', False),
        ('file0.txt', True),
        ('file1.txt', True),
        ('file2.txt', False),
        ('file3.txt', False),
    ])
    def test_access_images(self, filename, expected):
        urlname = 'sharednote-image-by-name' if 'img' in filename else 'sharednote-file-by-name'
        res = self.client.get(reverse(urlname, kwargs={'shareinfo_pk': self.share_info.id, 'filename': filename}))
        assert res.status_code == (200 if expected else 404)

    def test_comment(self):
        user = create_user()
        client_user = api_client(user=user)
        self.project.members.create(user=user)

        # Test authenticated access
        comment_text = 'Initial comment'
        client_user.patch(reverse('projectnoteshareinfo-detail', kwargs={'project_pk': self.project.id, 'note_id': self.note_shared.note_id, 'pk': self.share_info.id}), data={
            'comment': comment_text,
        })
        res_auth = client_user.get(reverse('projectnoteshareinfo-detail', kwargs={'project_pk': self.project.id, 'note_id': self.note_shared.note_id, 'pk': self.share_info.id}))
        assert res_auth.data['comment'] == comment_text

        # Test unauthenticated access - comment field should NOT be present
        res_public = self.client.get(reverse('publicshareinfo-detail', kwargs={'pk': self.share_info.id}))
        assert res_public.status_code == 200
        assert 'comment' not in res_public.data


@pytest.mark.django_db()
class TestSharedUserNotePermissions:
    @pytest.fixture(autouse=True)
    @mock_time(before=timedelta(days=1))
    def setUp(self):
        self.user = create_user(
            notes_kwargs=[],
            images_kwargs=[{'name': f'img{i}.png'} for i in range(4)],
            files_kwargs=[{'name': f'file{i}.txt'} for i in range(4)])
        self.client = api_client(user=None)

        # Create user notes with images/files
        self.note_shared = create_usernotebookpage(user=self.user, text='![](/images/name/img0.png)\n[file](/files/name/file0.txt)')
        self.childnote_shared = create_usernotebookpage(user=self.user, parent=self.note_shared, text='![](/images/name/img1.png)\n[file](/files/name/file1.txt)')
        self.share_info = create_shareinfo(usernote=self.note_shared)

        self.note_not_shared = create_usernotebookpage(user=self.user, text='![](/images/name/img2.png)\n[file](/files/name/file2.txt)')
        self.childnote_not_shared = create_usernotebookpage(user=self.user, parent=self.note_not_shared)

    @pytest.mark.parametrize(('note', 'expected'), [
        ('note_shared', True),
        ('childnote_shared', True),
        ('note_not_shared', False),
        ('childnote_not_shared', False),
    ])
    def test_access(self, note, expected):
        note_id = getattr(self, note).note_id
        res = self.client.get(reverse('sharednote-detail', kwargs={'shareinfo_pk': self.share_info.id, 'id': note_id}))
        assert res.status_code == (200 if expected else 404), res.data

    @pytest.mark.parametrize(('parent', 'expected'), [
        ('note_shared', True),
        ('childnote_shared', True),
        ('note_not_shared', False),
        ('childnote_not_shared', False),
        (None, False),
    ])
    def test_create(self, parent, expected):
        parent_id = getattr(self, parent).note_id if parent else None
        data = self.client.get(reverse('sharednote-detail', kwargs={'shareinfo_pk': self.share_info.id, 'id': self.note_shared.note_id})).data
        res = self.client.post(reverse('sharednote-list', kwargs={'shareinfo_pk': self.share_info.id}), data=data | {
            'parent': parent_id,
        })
        assert res.status_code == (201 if expected else 400), res.data
        if expected:
            res_list = self.client.get(reverse('sharednote-list', kwargs={'shareinfo_pk': self.share_info.id}))
            assert res.data['id'] in [n['id'] for n in res_list.data]
            res_detail = self.client.get(reverse('sharednote-detail', kwargs={'shareinfo_pk': self.share_info.id, 'id': res.data['id']}))
            assert res_detail.status_code == 200

    @pytest.mark.parametrize(('note', 'expected'), [
        ('note_shared', False),
        ('childnote_shared', True),
        ('note_not_shared', False),
        ('childnote_not_shared', False),
    ])
    def test_delete(self, note, expected):
        note_id = getattr(self, note).note_id
        res = self.client.delete(reverse('sharednote-detail', kwargs={'shareinfo_pk': self.share_info.id, 'id': note_id}))
        assert res.status_code in ([204] if expected else [400, 404])

    def test_list_includes_only_childnotes(self):
        res = self.client.get(reverse('sharednote-list', kwargs={'shareinfo_pk': self.share_info.id}))
        assert set([n['id'] for n in res.data]) == {str(self.note_shared.note_id), str(self.childnote_shared.note_id)}

    def test_shared_childnote(self):
        update(self.note_shared, parent=self.note_not_shared)

        res = self.client.get(reverse('sharednote-list', kwargs={'shareinfo_pk': self.share_info.id}))
        assert set([n['id'] for n in res.data]) == {str(self.note_shared.note_id), str(self.childnote_shared.note_id)}

    @pytest.mark.parametrize(('filename', 'expected'), [
        ('img0.png', True),
        ('img1.png', True),
        ('img2.png', False),
        ('img3.png', False),
        ('file0.txt', True),
        ('file1.txt', True),
        ('file2.txt', False),
        ('file3.txt', False),
    ])
    def test_access_images(self, filename, expected):
        urlname = 'sharednote-image-by-name' if 'img' in filename else 'sharednote-file-by-name'
        res = self.client.get(reverse(urlname, kwargs={'shareinfo_pk': self.share_info.id, 'filename': filename}))
        assert res.status_code == (200 if expected else 404)

    def test_comment(self):
        client_user = api_client(user=self.user)

        # Test authenticated access
        comment_text = 'Initial comment'
        client_user.patch(reverse('usernoteshareinfo-detail', kwargs={'pentestuser_pk': self.user.id, 'note_id': self.note_shared.note_id, 'pk': self.share_info.id}), data={
            'comment': comment_text,
        })
        res_auth = client_user.get(reverse('usernoteshareinfo-detail', kwargs={'pentestuser_pk': self.user.id, 'note_id': self.note_shared.note_id, 'pk': self.share_info.id}))
        assert res_auth.data['comment'] == comment_text

        # Test unauthenticated access - comment field should NOT be present
        res_public = self.client.get(reverse('publicshareinfo-detail', kwargs={'pk': self.share_info.id}))
        assert res_public.status_code == 200
        assert 'comment' not in res_public.data


@pytest.mark.django_db()
class TestSharedNotePendingFileAccess:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.project = create_project(notes_kwargs=[], images_kwargs=[], files_kwargs=[])
        self.note_shared = create_projectnotebookpage(project=self.project, text='Shared note')
        self.share_info = create_shareinfo(projectnote=self.note_shared)
        self.client = api_client(user=None)

    @pytest.mark.parametrize(('via_share', 'same_session', 'after', 'expected'), [
        pytest.param(False, True, None, 404, id='unreferenced-project-file'),
        pytest.param(True, True, None, 200, id='same-session'),
        pytest.param(True, False, None, 404, id='other-session'),
        pytest.param(True, True, timedelta(minutes=2), 404, id='after-grace'),
    ])
    def test_pending_file_access(self, via_share, same_session, after, expected):
        name = 'pending.txt'
        if via_share:
            res = self.client.post(
                reverse('sharednote-upload-image-or-file', kwargs={'shareinfo_pk': self.share_info.id}),
                data={'name': name, 'file': SimpleUploadedFile(name=name, content=b'content')},
                format='multipart',
            )
            assert res.status_code == 201, res.data
            name = res.data['name']
        else:
            UploadedProjectFile.objects.create(
                linked_object=self.project,
                name=name,
                file=SimpleUploadedFile(name=name, content=b'content'),
            )

        client = self.client if same_session else api_client(user=None)
        url = reverse('sharednote-file-by-name', kwargs={'shareinfo_pk': self.share_info.id, 'filename': name})
        if after:
            with mock_time(after=after):
                res = client.get(url)
        else:
            res = client.get(url)
        assert res.status_code == expected


@pytest.mark.django_db()
class TestSharedNoteFileAuthorization:
    """
    Secure contract for public share file access:
    - Writable shares must not authorize existing unreferenced project/user files by editing note text.
    - Unauthorized and nonexistent filenames must both return 404 (no existence oracle).
    - Allowlist is seeded at share create, extended by share uploads and trusted member uploads from the note editor.
    """

    PROJECT_FILE = 'project.txt'
    PROJECT_IMAGE = 'project.png'
    SHARED_FILE = 'shared.txt'
    SHARED_IMAGE = 'shared.png'

    def _asset_url(self, share_info, filename):
        urlname = 'sharednote-image-by-name' if filename.endswith('.png') else 'sharednote-file-by-name'
        return reverse(urlname, kwargs={'shareinfo_pk': share_info.id, 'filename': filename})

    def _note_url(self, share_info, note_id):
        return reverse('sharednote-detail', kwargs={'shareinfo_pk': share_info.id, 'id': note_id})

    def _setup_share(self, share_type, *, permissions_write=True):
        shared_text = f'![](/images/name/{self.SHARED_IMAGE})\n[file](/files/name/{self.SHARED_FILE})'
        secret_text = f'![](/images/name/{self.PROJECT_IMAGE})\n[file](/files/name/{self.PROJECT_FILE})'
        if share_type == 'project':
            owner = create_project(
                notes_kwargs=[],
                images_kwargs=[
                    {'name': self.SHARED_IMAGE, 'content': create_png_file()},
                    {'name': self.PROJECT_IMAGE, 'content': SECRET_IMAGE_CONTENT},
                ],
                files_kwargs=[
                    {'name': self.SHARED_FILE, 'content': b'shared-ok'},
                    {'name': self.PROJECT_FILE, 'content': SECRET_FILE_CONTENT},
                ],
            )
            note_shared = create_projectnotebookpage(project=owner, text=shared_text)
            create_projectnotebookpage(project=owner, text=secret_text)
            share_info = create_shareinfo(projectnote=note_shared, permissions_write=permissions_write)
        else:
            owner = create_user(notes_kwargs=[], images_kwargs=[], files_kwargs=[])
            UploadedUserNotebookImage.objects.create(
                linked_object=owner, name=self.SHARED_IMAGE,
                file=SimpleUploadedFile(name=self.SHARED_IMAGE, content=create_png_file()),
            )
            UploadedUserNotebookImage.objects.create(
                linked_object=owner, name=self.PROJECT_IMAGE,
                file=SimpleUploadedFile(name=self.PROJECT_IMAGE, content=SECRET_IMAGE_CONTENT),
            )
            UploadedUserNotebookFile.objects.create(
                linked_object=owner, name=self.SHARED_FILE,
                file=SimpleUploadedFile(name=self.SHARED_FILE, content=b'shared-ok'),
            )
            UploadedUserNotebookFile.objects.create(
                linked_object=owner, name=self.PROJECT_FILE,
                file=SimpleUploadedFile(name=self.PROJECT_FILE, content=SECRET_FILE_CONTENT),
            )
            note_shared = create_usernotebookpage(user=owner, text=shared_text)
            create_usernotebookpage(user=owner, text=secret_text)
            share_info = create_shareinfo(usernote=note_shared, permissions_write=permissions_write)
        return owner, note_shared, share_info, api_client(user=None)

    @pytest.mark.parametrize('share_type', ['project', 'user'])
    @pytest.mark.parametrize(('filename', 'expected'), [
        (SHARED_FILE, 200),
        (SHARED_IMAGE, 200),
        (PROJECT_FILE, 404),
        (PROJECT_IMAGE, 404),
        ('missing-xyz.txt', 404),
        ('missing-xyz.png', 404),
    ])
    def test_public_download_authorization(self, share_type, filename, expected):
        _, _, share_info, client = self._setup_share(share_type, permissions_write=False)
        res = client.get(self._asset_url(share_info, filename))
        assert res.status_code == expected
        if expected == 200 and filename == self.SHARED_FILE:
            assert response_body(res) == b'shared-ok'
        if expected == 404 and filename == self.PROJECT_FILE:
            assert SECRET_FILE_CONTENT not in response_body(res)

    @pytest.mark.parametrize(('filename', 'patch_text', 'secret'), [
        (PROJECT_FILE, f'see attachment [x](/{PROJECT_FILE})', SECRET_FILE_CONTENT),
        (PROJECT_IMAGE, f'![](/images/name/{PROJECT_IMAGE})', SECRET_IMAGE_CONTENT),
    ])
    def test_writable_patch_cannot_authorize_unreferenced(self, filename, patch_text, secret):
        _, note_shared, share_info, client = self._setup_share('project', permissions_write=True)

        res_before = client.get(self._asset_url(share_info, filename))
        assert res_before.status_code != 200
        assert secret not in response_body(res_before)

        res_patch = client.patch(self._note_url(share_info, note_shared.note_id), data={'text': patch_text})
        assert res_patch.status_code == 200, res_patch.data

        res = client.get(self._asset_url(share_info, filename))
        assert res.status_code == 404
        assert secret not in response_body(res)

    def test_readonly_share_cannot_patch(self):
        _, note_shared, share_info, client = self._setup_share('project', permissions_write=False)

        res_patch = client.patch(self._note_url(share_info, note_shared.note_id), data={
            'text': f'see attachment [x](/{self.PROJECT_FILE})',
        })
        assert res_patch.status_code == 403

        res = client.get(self._asset_url(share_info, self.PROJECT_FILE))
        assert res.status_code == 404
        assert SECRET_FILE_CONTENT not in response_body(res)

    def test_allowed_file_ids_not_exposed(self):
        _, note_shared, share_info, client = self._setup_share('project', permissions_write=False)

        res_share = client.get(reverse('publicshareinfo-detail', kwargs={'pk': share_info.id}))
        assert res_share.status_code == 200
        assert 'allowed_file_ids' not in res_share.data
        assert 'pending_file_ids' not in res_share.data

        res_note = client.get(self._note_url(share_info, note_shared.note_id))
        assert res_note.status_code == 200
        assert 'allowed_file_ids' not in res_note.data
        assert 'pending_file_ids' not in res_note.data

    def test_authenticated_edit_does_not_expand_allowlist(self):
        """Poison + member save must not promote planted refs onto the allowlist."""
        project, note_shared, share_info, public_client = self._setup_share('project', permissions_write=True)
        member = create_user()
        project.members.create(user=member)
        auth_client = api_client(user=member)

        secret = project.files.get(name=self.PROJECT_FILE)
        assert secret.id not in share_info.allowed_file_ids

        res_poison = public_client.patch(self._note_url(share_info, note_shared.note_id), data={
            'text': note_shared.text + f'\n[file](/files/name/{self.PROJECT_FILE})',
        })
        assert res_poison.status_code == 200, res_poison.data
        assert public_client.get(self._asset_url(share_info, self.PROJECT_FILE)).status_code == 404

        res_patch = auth_client.patch(
            reverse('projectnotebookpage-detail', kwargs={'project_pk': project.id, 'id': note_shared.note_id}),
            data={'text': note_shared.text + f'\n[file](/files/name/{self.PROJECT_FILE})\nmember edit'},
        )
        assert res_patch.status_code == 200, res_patch.data

        share_info.refresh_from_db()
        assert secret.id not in share_info.allowed_file_ids
        res = public_client.get(self._asset_url(share_info, self.PROJECT_FILE))
        assert res.status_code == 404
        assert SECRET_FILE_CONTENT not in response_body(res)

    @pytest.mark.parametrize('case', ['shared_note', 'no_note_id', 'other_note'])
    def test_upload_allowlist(self, case):
        project, note_shared, share_info, public_client = self._setup_share('project', permissions_write=True)
        member = create_user()
        project.members.create(user=member)
        auth_client = api_client(user=member)

        upload_name = f'{case}.png'
        data = {
            'name': upload_name,
            'file': SimpleUploadedFile(name=upload_name, content=create_png_file()),
        }
        if case == 'shared_note':
            data['note_id'] = str(note_shared.note_id)
        elif case == 'other_note':
            data['note_id'] = str(create_projectnotebookpage(project=project, text='other note').note_id)

        res_upload = auth_client.post(
            reverse('pentestproject-upload-image-or-file', kwargs={'pk': project.id}),
            data=data,
            format='multipart',
        )
        assert res_upload.status_code == 201, res_upload.data
        upload_name = res_upload.data['name']
        share_info.refresh_from_db()
        in_allowlist = any(str(fid) == str(res_upload.data['id']) for fid in share_info.allowed_file_ids)

        if case == 'shared_note':
            assert in_allowlist
            assert public_client.get(self._asset_url(share_info, upload_name)).status_code == 404
            res_patch = auth_client.patch(
                reverse('projectnotebookpage-detail', kwargs={'project_pk': project.id, 'id': note_shared.note_id}),
                data={'text': note_shared.text + f'\n![](/images/name/{upload_name})'},
            )
            assert res_patch.status_code == 200, res_patch.data
            assert public_client.get(self._asset_url(share_info, upload_name)).status_code == 200
        else:
            assert not in_allowlist

    @pytest.mark.parametrize('case', ['seeded', 'public_upload', 'blocked_secret'])
    def test_excalidraw_allowlist(self, case):
        if case == 'seeded':
            project = create_project(
                notes_kwargs=[],
                images_kwargs=[{'name': self.SHARED_IMAGE, 'content': create_png_file()}],
                files_kwargs=[],
            )
            note_shared = create_projectnotebookpage(
                project=project,
                type=NoteType.EXCALIDRAW,
                excalidraw_data={'elements': [
                    {'id': 'e1', 'type': 'image', 'fileId': self.SHARED_IMAGE, 'isDeleted': False},
                ]},
            )
            share_info = create_shareinfo(projectnote=note_shared, permissions_write=False)
            assert project.images.get(name=self.SHARED_IMAGE).id in share_info.allowed_file_ids
            assert api_client(user=None).get(self._asset_url(share_info, self.SHARED_IMAGE)).status_code == 200
            return

        if case == 'public_upload':
            project = create_project(notes_kwargs=[], images_kwargs=[], files_kwargs=[])
            excalidraw_note = create_projectnotebookpage(project=project, type=NoteType.EXCALIDRAW)
            share_info = create_shareinfo(projectnote=excalidraw_note, permissions_write=True)
            client = api_client(user=None)
            res_upload = client.post(
                reverse('sharednote-upload-image-or-file', kwargs={'shareinfo_pk': share_info.id}),
                data={
                    'file': SimpleUploadedFile(name='excal-public.png', content=create_png_file()),
                    'note_id': str(excalidraw_note.note_id),
                },
                format='multipart',
            )
            assert res_upload.status_code == 201, res_upload.data
            share_info.refresh_from_db()
            assert any(str(fid) == str(res_upload.data['id']) for fid in share_info.allowed_file_ids)
            assert client.get(self._asset_url(share_info, res_upload.data['name'])).status_code == 200
            return

        # blocked_secret
        project, note_shared, share_info, client = self._setup_share('project', permissions_write=True)
        assert project.images.get(name=self.PROJECT_IMAGE).id not in share_info.allowed_file_ids
        create_projectnotebookpage(
            project=project,
            parent=note_shared,
            type=NoteType.EXCALIDRAW,
            excalidraw_data={'elements': [
                {'id': 'e1', 'type': 'image', 'fileId': self.PROJECT_IMAGE, 'isDeleted': False},
            ]},
        )
        res = client.get(self._asset_url(share_info, self.PROJECT_IMAGE))
        assert res.status_code == 404
        assert SECRET_IMAGE_CONTENT not in response_body(res)

    def test_unlink_and_prune(self):
        project, note_shared, share_info, client = self._setup_share('project', permissions_write=True)
        member = create_user()
        project.members.create(user=member)
        auth_client = api_client(user=member)

        shared_file = project.files.get(name=self.SHARED_FILE)
        assert shared_file.id in share_info.allowed_file_ids
        assert client.get(self._asset_url(share_info, self.SHARED_FILE)).status_code == 200

        res_unlink = auth_client.patch(
            reverse('projectnotebookpage-detail', kwargs={'project_pk': project.id, 'id': note_shared.note_id}),
            data={'text': 'no attachments'},
        )
        assert res_unlink.status_code == 200, res_unlink.data
        # Live reference check blocks download; allowlist prune may be deferred to the daily job.
        assert client.get(self._asset_url(share_info, self.SHARED_FILE)).status_code == 404

        res_readd = auth_client.patch(
            reverse('projectnotebookpage-detail', kwargs={'project_pk': project.id, 'id': note_shared.note_id}),
            data={'text': f'[file](/files/name/{self.SHARED_FILE})'},
        )
        assert res_readd.status_code == 200, res_readd.data
        # Previously allowlisted files remain downloadable if re-linked before prune.
        share_info.refresh_from_db()
        assert shared_file.id in share_info.allowed_file_ids
        assert client.get(self._asset_url(share_info, self.SHARED_FILE)).status_code == 200

        shared_file.delete()
        share_info.refresh_from_db()
        assert shared_file.id not in share_info.allowed_file_ids
        assert client.get(self._asset_url(share_info, self.SHARED_FILE)).status_code == 404


@pytest.mark.django_db()
class TestSharedNotePendingFileIds:
    PROJECT_FILE = TestSharedNoteFileAuthorization.PROJECT_FILE
    PROJECT_IMAGE = TestSharedNoteFileAuthorization.PROJECT_IMAGE
    SHARED_FILE = TestSharedNoteFileAuthorization.SHARED_FILE
    SHARED_IMAGE = TestSharedNoteFileAuthorization.SHARED_IMAGE

    def _setup_share(self, share_type, *, permissions_write=True):
        return TestSharedNoteFileAuthorization()._setup_share(share_type, permissions_write=permissions_write)

    def _asset_url(self, share_info, filename):
        return TestSharedNoteFileAuthorization()._asset_url(share_info, filename)

    def _note_url(self, share_info, note_id):
        return TestSharedNoteFileAuthorization()._note_url(share_info, note_id)

    def _secret_asset(self, owner, share_type, filename):
        if share_type == 'project':
            if filename.endswith('.png'):
                return owner.images.get(name=filename)
            return owner.files.get(name=filename)
        if filename.endswith('.png'):
            return UploadedUserNotebookImage.objects.get(linked_object=owner, name=filename)
        return UploadedUserNotebookFile.objects.get(linked_object=owner, name=filename)

    @pytest.mark.parametrize('share_type', ['project', 'user'])
    @pytest.mark.parametrize(('filename', 'patch_text'), [
        (TestSharedNoteFileAuthorization.PROJECT_FILE, f'see attachment [x](/files/name/{TestSharedNoteFileAuthorization.PROJECT_FILE})'),
        (TestSharedNoteFileAuthorization.PROJECT_IMAGE, f'![](/images/name/{TestSharedNoteFileAuthorization.PROJECT_IMAGE})'),
    ])
    def test_public_patch_adds_pending_file(self, share_type, filename, patch_text):
        owner, note_shared, share_info, client = self._setup_share(share_type, permissions_write=True)
        secret = self._secret_asset(owner, share_type, filename)
        assert secret.id not in share_info.allowed_file_ids
        assert secret.id not in share_info.pending_file_ids

        res_patch = client.patch(self._note_url(share_info, note_shared.note_id), data={'text': patch_text})
        assert res_patch.status_code == 200, res_patch.data

        share_info.refresh_from_db()
        assert secret.id in share_info.pending_file_ids
        assert secret.id not in share_info.allowed_file_ids
        assert client.get(self._asset_url(share_info, filename)).status_code == 404

    @pytest.mark.parametrize('share_type', ['project', 'user'])
    def test_authenticated_edit_adds_pending_file(self, share_type):
        owner, note_shared, share_info, public_client = self._setup_share(share_type, permissions_write=True)
        secret = self._secret_asset(owner, share_type, self.PROJECT_FILE)
        if share_type == 'project':
            member = create_user()
            owner.members.create(user=member)
            detail_url = reverse(
                'projectnotebookpage-detail',
                kwargs={'project_pk': owner.id, 'id': note_shared.note_id},
            )
        else:
            member = owner
            detail_url = reverse(
                'usernotebookpage-detail',
                kwargs={'pentestuser_pk': owner.id, 'id': note_shared.note_id},
            )
        auth_client = api_client(user=member)

        res_patch = auth_client.patch(
            detail_url,
            data={'text': note_shared.text + f'\n[file](/files/name/{self.PROJECT_FILE})'},
        )
        assert res_patch.status_code == 200, res_patch.data

        share_info.refresh_from_db()
        assert secret.id in share_info.pending_file_ids
        assert secret.id not in share_info.allowed_file_ids
        assert public_client.get(self._asset_url(share_info, self.PROJECT_FILE)).status_code == 404

    def test_excalidraw_reference_adds_pending_file(self):
        project, note_shared, share_info, client = self._setup_share('project', permissions_write=True)
        secret = project.images.get(name=self.PROJECT_IMAGE)
        assert secret.id not in share_info.allowed_file_ids

        res_create = client.post(
            reverse('sharednote-list', kwargs={'shareinfo_pk': share_info.id}),
            data={
                'type': NoteType.EXCALIDRAW,
                'parent': str(note_shared.note_id),
                'title': 'Excalidraw child',
                'excalidraw_data': {'elements': [
                    {'id': 'e1', 'type': 'image', 'fileId': self.PROJECT_IMAGE, 'isDeleted': False},
                ]},
            },
        )
        assert res_create.status_code == 201, res_create.data

        share_info.refresh_from_db()
        assert secret.id in share_info.pending_file_ids
        assert secret.id not in share_info.allowed_file_ids
        assert client.get(self._asset_url(share_info, self.PROJECT_IMAGE)).status_code == 404

    def test_upload_does_not_add_pending(self):
        project, note_shared, share_info, public_client = self._setup_share('project', permissions_write=True)
        res_upload = public_client.post(
            reverse('sharednote-upload-image-or-file', kwargs={'shareinfo_pk': share_info.id}),
            data={
                'file': SimpleUploadedFile(name='upload-pending.png', content=create_png_file()),
                'note_id': str(note_shared.note_id),
            },
            format='multipart',
        )
        assert res_upload.status_code == 201, res_upload.data
        share_info.refresh_from_db()
        upload_id = res_upload.data['id']
        assert any(str(fid) == str(upload_id) for fid in share_info.allowed_file_ids)
        assert not any(str(fid) == str(upload_id) for fid in share_info.pending_file_ids)

    def test_pending_file_ids_exposed_to_members(self):
        project, note_shared, share_info, _ = self._setup_share('project', permissions_write=False)
        member = create_user()
        project.members.create(user=member)
        auth_client = api_client(user=member)

        res = auth_client.get(reverse(
            'projectnoteshareinfo-detail',
            kwargs={'project_pk': project.id, 'note_id': note_shared.note_id, 'pk': share_info.id},
        ))
        assert res.status_code == 200
        assert 'pending_file_ids' in res.data

    def _approve_pending_url(self, share_type, owner, note_shared, share_info):
        if share_type == 'project':
            return reverse(
                'projectnoteshareinfo-approve-pending-files',
                kwargs={'project_pk': owner.id, 'note_id': note_shared.note_id, 'pk': share_info.id},
            )
        return reverse(
            'usernoteshareinfo-approve-pending-files',
            kwargs={'pentestuser_pk': owner.id, 'note_id': note_shared.note_id, 'pk': share_info.id},
        )

    @pytest.mark.parametrize(('share_type', 'via'), [
        ('project', 'member'),
        ('user', 'member'),
        ('project', 'share_visitor'),
        ('user', 'share_visitor'),
        ('project', 'guest_member'),
    ])
    def test_approve_pending_files(self, share_type, via):
        owner, note_shared, share_info, public_client = self._setup_share(share_type, permissions_write=True)
        secret_file = self._secret_asset(owner, share_type, self.PROJECT_FILE)
        secret_image = self._secret_asset(owner, share_type, self.PROJECT_IMAGE)

        if via == 'member':
            if share_type == 'project':
                member = create_user()
                owner.members.create(user=member)
                client = api_client(user=member)
            else:
                client = api_client(user=owner)
        elif via == 'guest_member':
            guest = create_user(is_guest=True)
            owner.members.create(user=guest)
            client = api_client(user=guest)
        else:
            client = public_client

        public_client.patch(
            self._note_url(share_info, note_shared.note_id),
            data={'text': note_shared.text + f'\n[file](/files/name/{self.PROJECT_FILE})\n![](/images/name/{self.PROJECT_IMAGE})'},
        )
        share_info.refresh_from_db()
        assert secret_file.id in share_info.pending_file_ids
        assert secret_image.id in share_info.pending_file_ids
        assert public_client.get(self._asset_url(share_info, self.PROJECT_FILE)).status_code == 404

        res = client.post(
            self._approve_pending_url(share_type, owner, note_shared, share_info),
            data={'file_ids': [str(secret_file.id), str(secret_image.id)]},
        )

        share_info.refresh_from_db()
        if via == 'member':
            assert res.status_code == 200, res.data
            assert secret_file.id not in res.data['pending_file_ids']
            assert secret_image.id not in res.data['pending_file_ids']
            assert secret_file.id in share_info.allowed_file_ids
            assert secret_image.id in share_info.allowed_file_ids
            assert secret_file.id not in share_info.pending_file_ids
            assert secret_image.id not in share_info.pending_file_ids
            assert public_client.get(self._asset_url(share_info, self.PROJECT_FILE)).status_code == 200
            assert public_client.get(self._asset_url(share_info, self.PROJECT_IMAGE)).status_code == 200
        else:
            assert res.status_code in [401, 403], res.data
            assert secret_file.id in share_info.pending_file_ids
            assert secret_image.id in share_info.pending_file_ids
            assert secret_file.id not in share_info.allowed_file_ids
            assert secret_image.id not in share_info.allowed_file_ids
            assert public_client.get(self._asset_url(share_info, self.PROJECT_FILE)).status_code == 404
            assert public_client.get(self._asset_url(share_info, self.PROJECT_IMAGE)).status_code == 404

    @pytest.mark.parametrize('share_type', ['project', 'user'])
    def test_approve_pending_files_rejects_non_pending(self, share_type):
        owner, note_shared, share_info, public_client = self._setup_share(share_type, permissions_write=True)
        secret = self._secret_asset(owner, share_type, self.PROJECT_FILE)

        if share_type == 'project':
            member = create_user()
            owner.members.create(user=member)
            auth_client = api_client(user=member)
        else:
            auth_client = api_client(user=owner)

        public_client.patch(
            self._note_url(share_info, note_shared.note_id),
            data={'text': note_shared.text + f'\n[file](/files/name/{self.PROJECT_FILE})'},
        )
        share_info.refresh_from_db()
        assert secret.id in share_info.pending_file_ids

        res = auth_client.post(
            self._approve_pending_url(share_type, owner, note_shared, share_info),
            data={'file_ids': [str(secret.id), str(uuid4())]},
        )
        assert res.status_code == 400, res.data

        share_info.refresh_from_db()
        assert secret.id in share_info.pending_file_ids
        assert secret.id not in share_info.allowed_file_ids

    def test_prune_removes_unreferenced_pending(self):
        project, note_shared, share_info, client = self._setup_share('project', permissions_write=True)
        secret = project.files.get(name=self.PROJECT_FILE)
        assert secret.id not in share_info.allowed_file_ids

        res_patch = client.patch(
            self._note_url(share_info, note_shared.note_id),
            data={'text': note_shared.text + f'\n[file](/files/name/{self.PROJECT_FILE})'},
        )
        assert res_patch.status_code == 200, res_patch.data
        share_info.refresh_from_db()
        assert secret.id in share_info.pending_file_ids

        note_shared.refresh_from_db()
        note_shared.text = 'no attachments'
        note_shared.save()
        share_info.refresh_from_db()
        assert secret.id in share_info.pending_file_ids

        TestPeriodicShareAllowlistPrune()._run_prune(last_success=None)
        share_info.refresh_from_db()
        assert secret.id not in share_info.pending_file_ids
        assert project.files.filter(pk=secret.pk).exists()


@pytest.mark.django_db()
class TestSharedNotePendingFileIdsWithDbEncryption:
    PROJECT_FILE = TestSharedNoteFileAuthorization.PROJECT_FILE
    PROJECT_IMAGE = TestSharedNoteFileAuthorization.PROJECT_IMAGE

    @pytest.fixture(autouse=True)
    def enable_db_encryption(self):
        with override_settings(
            ENCRYPTION_KEYS={'test-key': crypto.EncryptionKey(id='test-key', key=b'a' * 32)},
            DEFAULT_ENCRYPTION_KEY_ID='test-key',
            ENCRYPTION_PLAINTEXT_FALLBACK=True,
        ):
            yield

    def _setup_share(self, share_type, *, permissions_write=True):
        return TestSharedNoteFileAuthorization()._setup_share(share_type, permissions_write=permissions_write)

    def _secret_asset(self, owner, share_type, filename):
        if share_type == 'project':
            if filename.endswith('.png'):
                return owner.images.filter_name(filename).get()
            return owner.files.filter_name(filename).get()
        if filename.endswith('.png'):
            return UploadedUserNotebookImage.objects.filter(linked_object=owner).filter_name(filename).get()
        return UploadedUserNotebookFile.objects.filter(linked_object=owner).filter_name(filename).get()

    def _file_queryset(self, owner, share_type):
        if share_type == 'project':
            return owner.files
        return UploadedUserNotebookFile.objects.filter(linked_object=owner)

    @pytest.mark.parametrize('share_type', ['project', 'user'])
    def test_track_pending_files_by_names_with_encrypted_file_names(self, share_type):
        owner, note_shared, share_info, _ = self._setup_share(share_type, permissions_write=True)
        secret = self._secret_asset(owner, share_type, self.PROJECT_FILE)
        assert secret.id not in share_info.pending_file_ids

        if share_type == 'project':
            assert_db_field_encrypted(UploadedProjectFile.objects.filter(id=secret.id).values('name'), True)
        else:
            assert_db_field_encrypted(UploadedUserNotebookFile.objects.filter(id=secret.id).values('name'), True)

        files_qs = self._file_queryset(owner, share_type)
        assert not files_qs.filter(name=secret.name).exists()
        assert files_qs.filter_name(secret.name).exists()

        updated = ShareInfo.objects.track_pending_files_by_names(
            note_shared, {secret.name}, broadcast=False,
        )
        assert updated is True

        share_info.refresh_from_db()
        assert secret.id in share_info.pending_file_ids
        assert secret.id not in share_info.allowed_file_ids


@pytest.mark.django_db()
class TestPeriodicShareAllowlistPrune:
    """Daily cleanup prunes allowlists after note unlinks (REST or collab)."""

    SHARED_FILE = 'shared.txt'

    def _run_prune(self, last_success=None):
        from asgiref.sync import async_to_sync

        from sysreptor.pentests.tasks import prune_share_allowlists
        from sysreptor.tasks.models import PeriodicTask, PeriodicTaskInfo, periodic_task_registry

        async_to_sync(prune_share_allowlists)(task_info=PeriodicTaskInfo(
            spec=next(filter(lambda t: t.id == 'cleanup_unreferenced_images_and_files', periodic_task_registry.tasks)),
            model=PeriodicTask(last_success=last_success),
        ))

    def test_prune_while_file_still_on_non_shared_note(self):
        project = create_project(
            notes_kwargs=[],
            images_kwargs=[],
            files_kwargs=[{'name': self.SHARED_FILE, 'content': b'shared-ok'}],
        )
        note_shared = create_projectnotebookpage(
            project=project,
            text=f'[file](/files/name/{self.SHARED_FILE})',
        )
        create_projectnotebookpage(
            project=project,
            text=f'still used here [file](/files/name/{self.SHARED_FILE})',
        )
        share_info = create_shareinfo(projectnote=note_shared, permissions_write=False)
        shared_file = project.files.get(name=self.SHARED_FILE)
        assert shared_file.id in share_info.allowed_file_ids

        # Unlink without note-delete/file-delete prune hooks (same as collab or REST edit)
        note_shared.text = 'no attachments'
        note_shared.save()
        share_info.refresh_from_db()
        assert shared_file.id in share_info.allowed_file_ids

        self._run_prune(last_success=None)

        share_info.refresh_from_db()
        assert shared_file.id not in share_info.allowed_file_ids
        assert project.files.filter(pk=shared_file.pk).exists()

        note_shared.text = f'[file](/files/name/{self.SHARED_FILE})'
        note_shared.save()
        client = api_client(user=None)
        res = client.get(reverse(
            'sharednote-file-by-name',
            kwargs={'shareinfo_pk': share_info.id, 'filename': self.SHARED_FILE},
        ))
        assert res.status_code == 404

    def test_last_success_skips_unchanged_shares(self):
        project = create_project(
            notes_kwargs=[],
            images_kwargs=[],
            files_kwargs=[{'name': self.SHARED_FILE, 'content': b'shared-ok'}],
        )
        note_shared = create_projectnotebookpage(
            project=project,
            text=f'[file](/files/name/{self.SHARED_FILE})',
        )
        share_info = create_shareinfo(projectnote=note_shared, permissions_write=False)
        shared_file = project.files.get(name=self.SHARED_FILE)
        assert shared_file.id in share_info.allowed_file_ids

        note_shared.text = 'unlinked'
        note_shared.save()
        note_shared.refresh_from_db()

        # Notes were updated at last_success, not after → share excluded (updated__gt is strict)
        self._run_prune(last_success=note_shared.updated)
        share_info.refresh_from_db()
        assert shared_file.id in share_info.allowed_file_ids

        # Full / older last_success still prunes
        self._run_prune(last_success=None)
        share_info.refresh_from_db()
        assert shared_file.id not in share_info.allowed_file_ids


@pytest.mark.django_db()
class TestSharePasswordAuth:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.project = create_project(notes_kwargs=[{'text': 'text'}])
        self.note = self.project.notes.first()
        self.password = 'password'  # noqa: S105
        self.share_info = create_shareinfo(projectnote=self.note, password=self.password)
        self.client = api_client(user=None)

    def test_password_required(self):
        res = self.client.get(reverse('publicshareinfo-detail', kwargs={'pk': self.share_info.id}))
        assert res.status_code == 200
        assert res.data['password_required']

        res = self.client.get(reverse('sharednote-detail', kwargs={'shareinfo_pk': self.share_info.id, 'id': self.note.note_id}))
        assert res.status_code == 403

    def test_password_invalid(self):
        res = self.client.post(reverse('publicshareinfo-auth', kwargs={'pk': self.share_info.id}), data={'password': 'invalid'})
        assert res.status_code == 400

        res = self.client.get(reverse('sharednote-detail', kwargs={'shareinfo_pk': self.share_info.id, 'id': self.note.note_id}))
        assert res.status_code == 403

    def test_password_valid(self):
        res = self.client.post(reverse('publicshareinfo-auth', kwargs={'pk': self.share_info.id}), data={'password': self.password})
        assert res.status_code == 200

        res = self.client.get(reverse('sharednote-detail', kwargs={'shareinfo_pk': self.share_info.id, 'id': self.note.note_id}))
        assert res.status_code == 200

        # Other share: no access
        share_info_other = create_shareinfo(projectnote=self.note, password=self.password + 'other')
        res = self.client.get(reverse('sharednote-detail', kwargs={'shareinfo_pk': share_info_other.id, 'id': self.note.note_id}))
        assert res.status_code == 403

    def test_password_brute_force_protection(self):
        with override_settings(SHARING_MAX_FAILED_PASSWORD_ATTEMPTS=1):
            res = self.client.post(reverse('publicshareinfo-auth', kwargs={'pk': self.share_info.id}), data={'password': 'invalid'})
            assert res.status_code == 400

            # Locked
            self.share_info.refresh_from_db()
            assert self.share_info.failed_password_attempts == 1
            assert self.share_info.is_revoked
            assert not self.share_info.is_active

            res = self.client.post(reverse('publicshareinfo-auth', kwargs={'pk': self.share_info.id}), data={'password': self.password})
            assert res.status_code == 404

            # Unlock
            self.share_info.clear_changed_fields()
            self.share_info = update(self.share_info, is_revoked=False)

            assert self.share_info.failed_password_attempts == 0
            res = self.client.post(reverse('publicshareinfo-auth', kwargs={'pk': self.share_info.id}), data={'password': self.password})
            assert res.status_code == 200

    def test_share_auth_cycles_session_key(self):
        old_session_key = self.client.session.session_key
        res = self.client.post(reverse('publicshareinfo-auth', kwargs={'pk': self.share_info.id}), data={'password': self.password})
        assert res.status_code == 200
        assert self.client.session.session_key != old_session_key

        res = self.client.get(reverse('sharednote-detail', kwargs={'shareinfo_pk': self.share_info.id, 'id': self.note.note_id}))
        assert res.status_code == 200

    def test_share_auth_prevents_session_fixation(self):
        attacker_client = api_client(user=None)
        attacker_client.get(reverse('publicshareinfo-detail', kwargs={'pk': self.share_info.id}))
        fixed_session_key = attacker_client.session.session_key

        victim_client = api_client(user=None)
        victim_client.cookies[settings.SESSION_COOKIE_NAME] = fixed_session_key

        res = victim_client.post(reverse('publicshareinfo-auth', kwargs={'pk': self.share_info.id}), data={'password': self.password})
        assert res.status_code == 200
        assert victim_client.session.session_key != fixed_session_key

        note_url = reverse('sharednote-detail', kwargs={'shareinfo_pk': self.share_info.id, 'id': self.note.note_id})
        res = attacker_client.get(note_url)
        assert res.status_code == 403

        res = victim_client.get(note_url)
        assert res.status_code == 200
