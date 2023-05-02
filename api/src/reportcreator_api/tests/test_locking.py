import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework.test import APIClient
from reportcreator_api.pentests.models import LockStatus
from reportcreator_api.tests.mock import create_project, create_user, mock_time


@pytest.mark.django_db
class TestLocking:
    @pytest.fixture(autouse=True)
    def setUp(self) -> None:
        self.user1 = create_user()
        self.user2 = create_user()
        self.project = create_project(members=[self.user1, self.user2])
        self.finding = self.project.findings.first()
        self.section = self.project.sections.first()
    
    def test_locking(self):
        assert self.finding.lock(user=self.user1) == LockStatus.CREATED
        assert self.finding.is_locked
        assert self.finding.lock_info_data.user == self.user1
        assert self.finding.lock(user=self.user1) == LockStatus.REFRESHED
        assert self.finding.lock(user=self.user2) == LockStatus.FAILED
        assert self.finding.unlock(user=self.user2) == False
        assert self.finding.unlock(user=self.user1) == True
        assert self.finding.lock(user=self.user2) == LockStatus.CREATED

        with mock_time(after=settings.MAX_LOCK_TIME * 2):
            assert not self.finding.is_locked
            assert self.finding.lock(user=self.user2) == LockStatus.CREATED

    def assert_api_locking(self, obj, url_basename, url_kwargs):
        client_u1 = APIClient()
        client_u1.force_authenticate(user=self.user1)
        client_u2 = APIClient()
        client_u2.force_authenticate(user=self.user2)

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

    def test_api_lock_finding(self):
        self.assert_api_locking(obj=self.finding, url_basename='finding', url_kwargs={'project_pk': self.project.pk, 'finding_id': self.finding.finding_id})
    
    def test_api_lock_section(self):
        self.assert_api_locking(obj=self.section, url_basename='section', url_kwargs={'project_pk': self.project.pk, 'section_id': self.section.section_id})

