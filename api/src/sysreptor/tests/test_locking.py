import pytest
from django.conf import settings
from django.urls import reverse

from sysreptor.pentests.models import Language, LockStatus
from sysreptor.tests.mock import (
    api_client,
    create_project_type,
    create_template,
    create_user,
    mock_time,
)


@pytest.mark.django_db()
class TestLocking:
    @pytest.fixture(autouse=True)
    def setUp(self) -> None:
        self.user1 = create_user(is_template_editor=True, is_designer=True)
        self.user2 = create_user(is_template_editor=True, is_designer=True)
        self.project_type = create_project_type()
        self.template = create_template()

    def test_locking(self):
        assert self.project_type.lock(user=self.user1) == LockStatus.CREATED
        assert self.project_type.is_locked
        assert self.project_type.lock_info_data.user == self.user1
        assert self.project_type.lock(user=self.user1) == LockStatus.REFRESHED
        assert self.project_type.lock(user=self.user2) == LockStatus.FAILED
        assert self.project_type.unlock(user=self.user2) is False
        assert self.project_type.unlock(user=self.user1) is True
        assert self.project_type.lock(user=self.user2) == LockStatus.CREATED

        with mock_time(after=settings.MAX_LOCK_TIME * 2):
            assert not self.project_type.is_locked
            assert self.project_type.lock(user=self.user2) == LockStatus.CREATED

    def assert_api_locking(self, obj, url_basename, url_kwargs):
        client_u1 = api_client(self.user1)
        client_u2 = api_client(self.user2)

        # Lock and update
        assert client_u1.post(reverse(url_basename + '-lock', kwargs=url_kwargs)).status_code == 201
        obj = obj.__class__.objects.get(pk=obj.pk)
        assert obj.is_locked
        assert obj.lock_info_data.user == self.user1
        assert client_u1.post(reverse(url_basename + '-lock', kwargs=url_kwargs)).status_code == 200
        assert client_u1.patch(reverse(url_basename + '-detail', kwargs=url_kwargs), data={}).status_code == 200

        # Other user
        assert client_u2.patch(reverse(url_basename + '-detail', kwargs=url_kwargs), data={}).status_code == 403
        assert client_u2.post(reverse(url_basename + '-lock', kwargs=url_kwargs)).status_code == 403
        assert client_u2.post(reverse(url_basename + '-unlock', kwargs=url_kwargs)).status_code == 403

        # Unlock
        assert client_u1.post(reverse(url_basename + '-unlock', kwargs=url_kwargs)).status_code == 200
        obj = obj.__class__.objects.get(pk=obj.pk)
        assert not obj.is_locked

        # Update without locking
        assert client_u2.patch(reverse(url_basename + '-detail', kwargs=url_kwargs), data={}).status_code == 200
        obj = obj.__class__.objects.get(pk=obj.pk)
        assert not obj.is_locked

    def test_lock_project_type(self):
        self.assert_api_locking(obj=self.project_type, url_basename='projecttype', url_kwargs={'pk': self.project_type.id})

    def test_api_lock_template(self):
        self.assert_api_locking(obj=self.template, url_basename='findingtemplate', url_kwargs={'pk': self.template.id})

    def test_api_lock_template_translation(self):
        self.template.lock(self.user1)

        client_u1 = api_client(self.user1)
        assert client_u1.patch(reverse('findingtemplatetranslation-detail', kwargs={'template_pk': self.template.id, 'pk': self.template.main_translation.id}), data={}).status_code == 200
        res_create = client_u1.post(reverse('findingtemplatetranslation-list', kwargs={'template_pk': self.template.id}), data={
            'language': Language.FRENCH_FR,
            'data': {'title': 'French template'},
        })
        assert res_create.status_code == 201

        client_u2 = api_client(self.user2)
        assert client_u2.patch(reverse('findingtemplatetranslation-detail', kwargs={'template_pk': self.template.id, 'pk': self.template.main_translation.id}), data={}).status_code == 403
        assert client_u2.post(reverse('findingtemplatetranslation-list', kwargs={'template_pk': self.template.id}), data={
            'language': Language.SPANISH,
            'data': {'title': 'Spanish template'},
        }).status_code == 403
        assert client_u2.delete(reverse('findingtemplatetranslation-detail', kwargs={'template_pk': self.template.id, 'pk': res_create.data['id']})).status_code == 403

        assert client_u1.delete(reverse('findingtemplatetranslation-detail', kwargs={'template_pk': self.template.id, 'pk': res_create.data['id']})).status_code == 204

