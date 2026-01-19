import pytest
from django.test import override_settings
from django.urls import reverse

from sysreptor.tests.mock import (
    api_client,
    create_project,
    create_projectnotebookpage,
    create_shareinfo,
    create_user,
    update,
)


@pytest.mark.django_db()
class TestSharedPermissions:
    @pytest.fixture(autouse=True)
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
        assert res.status_code == (200 if expected else 403)

    def test_comment(self):
        user = create_user()
        client_user = api_client(user=user)
        self.project.members.create(user=user)

        # Test authenticated access
        comment_text = 'Initial comment'
        client_user.patch(reverse('shareinfo-detail', kwargs={'project_pk': self.project.id, 'note_id': self.note_shared.note_id, 'pk': self.share_info.id}), data={
            'comment': comment_text,
        })
        res_auth = client_user.get(reverse('shareinfo-detail', kwargs={'project_pk': self.project.id, 'note_id': self.note_shared.note_id, 'pk': self.share_info.id}))
        assert res_auth.data['comment'] == comment_text

        # Test unauthenticated access - comment field should NOT be present
        res_public = self.client.get(reverse('publicshareinfo-detail', kwargs={'pk': self.share_info.id}))
        assert res_public.status_code == 200
        assert 'comment' not in res_public.data


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
