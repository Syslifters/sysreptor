import pytest
from asgiref.sync import async_to_sync
from datetime import timedelta
from unittest import mock
from pytest_django.asserts import assertNumQueries
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from reportcreator_api.tasks.models import PeriodicTask, TaskStatus
from reportcreator_api.pentests.models import PentestProject, ArchivedProject
from reportcreator_api.pentests.tasks import cleanup_project_files, cleanup_usernotebook_files, reset_stale_archive_restores, \
    automatically_archive_projects, automatically_delete_archived_projects
from reportcreator_api.tests.mock import create_archived_project, create_project, create_user, mock_time


def task_success():
    pass


def task_failure():
    raise Exception('Failed task')


@pytest.mark.django_db
class TestPeriodicTaskScheduling:
    @pytest.fixture(autouse=True)
    def setUp(self):
        with mock.patch('reportcreator_api.tests.test_periodic_tasks.task_success') as self.mock_task_success, \
             mock.patch('reportcreator_api.tests.test_periodic_tasks.task_failure', side_effect=Exception) as self.mock_task_failure, \
             override_settings(PERIODIC_TASKS=[
                {
                    'id': 'task_success', 
                    'task': 'reportcreator_api.tests.test_periodic_tasks.task_success',
                    'schedule': timedelta(days=1),
                },
                {
                    'id': 'task_failure',
                    'task': 'reportcreator_api.tests.test_periodic_tasks.task_failure',

                }
             ]):
            yield
    
    def run_tasks(self):
        res = APIClient().get(reverse('utils-healthcheck'))
        assert res.status_code == 200

    def test_initial_run(self):
        self.run_tasks()
        assert PeriodicTask.objects.all().count() == 2
        assert PeriodicTask.objects.get(id='task_success').status == TaskStatus.SUCCESS
        assert PeriodicTask.objects.get(id='task_failure').status == TaskStatus.FAILED
        assert self.mock_task_success.call_count == 1
        assert self.mock_task_failure.call_count == 1

    def test_not_rerun_until_schedule(self):
        prev = PeriodicTask.objects.create(id='task_success', status=TaskStatus.SUCCESS, started=timezone.now(), completed=timezone.now())
        self.run_tasks()
        t = PeriodicTask.objects.get(id='task_success')
        assert t.status == TaskStatus.SUCCESS
        assert t.started == prev.started
        assert not self.mock_task_success.called
    
    def test_rerun_after_schedule(self):
        PeriodicTask.objects.create(id='task_success', status=TaskStatus.SUCCESS, started=timezone.now() - timedelta(days=2), completed=timezone.now()- timedelta(days=2))
        start_time = timezone.now()
        self.run_tasks()
        t = PeriodicTask.objects.get(id='task_success')
        assert t.status == TaskStatus.SUCCESS
        assert t.started > start_time
        assert t.completed > start_time
        assert self.mock_task_success.call_count == 1
    
    def test_retry(self):
        PeriodicTask.objects.create(id='task_failure', status=TaskStatus.FAILED, started=timezone.now() - timedelta(hours=2), completed=timezone.now()- timedelta(hours=2))
        start_time = timezone.now()
        self.run_tasks()
        t = PeriodicTask.objects.get(id='task_failure')
        assert t.status == TaskStatus.FAILED
        assert t.started > start_time
        assert t.completed > start_time
        assert self.mock_task_failure.call_count == 1
        
    def test_running_not_scheduled(self):
        running = PeriodicTask.objects.create(id='task_success', status=TaskStatus.RUNNING, started=timezone.now())
        self.run_tasks()
        t = PeriodicTask.objects.get(id='task_success')
        assert t.status == TaskStatus.RUNNING
        assert t.started == running.started
        assert t.completed == running.completed
        assert not self.mock_task_success.called

    def test_running_timeout_retry(self):
        PeriodicTask.objects.create(id='task_success', status=TaskStatus.RUNNING, started=timezone.now() - timedelta(hours=2))
        start_time = timezone.now()
        self.run_tasks()
        t = PeriodicTask.objects.get(id='task_success')
        assert t.status == TaskStatus.SUCCESS
        assert t.started > start_time
        assert t.completed > start_time
        assert self.mock_task_success.call_count == 1

    def test_db_query_performance(self):
        self.run_tasks()

        with assertNumQueries(1):
            async_to_sync(PeriodicTask.objects.run_all_pending_tasks)()


@pytest.mark.django_db
class TestCleanupUnreferencedFiles:
    def file_exists(self, file_obj):
        try:
            file_obj.file.read()
            return True
        except FileNotFoundError:
            return False

    def run_cleanup_project_files(self, num_queries, last_success=None):
        with assertNumQueries(num_queries):
            async_to_sync(cleanup_project_files)(task_info={
                'model': PeriodicTask(last_success=last_success)
            })
    
    def run_cleanup_user_files(self, num_queries, last_success=None):
        with assertNumQueries(num_queries):
            async_to_sync(cleanup_usernotebook_files)(task_info={
                'model': PeriodicTask(last_success=last_success)
            })

    def test_unreferenced_files_removed(self):
        with mock_time(before=timedelta(days=10)):
            project = create_project(
                images_kwargs=[{'name': 'image.png'}],
                files_kwargs=[{'name': 'file.pdf'}]
            )
            project_image = project.images.first()
            project_file = project.files.first()
            user = create_user(
                images_kwargs=[{'name': 'image.png'}],
            )
            user_image = user.images.first()
        # self.run_cleanup(num_queries=2 + 6 + 3 * 2 + 3)
        self.run_cleanup_project_files(num_queries=1 + 4 + 2 * 2 + 2 * 1)
        self.run_cleanup_user_files(num_queries=1 + 2 + 1 * 2 + 1 * 1)
        # Deleted from DB
        assert project.images.count() == 0
        assert project.files.count() == 0
        assert user.images.count() == 0
        # Deleted from FS
        assert not self.file_exists(project_image)
        assert not self.file_exists(project_file)
        assert not self.file_exists(user_image)

    def test_recently_created_unreferenced_files_not_removed(self):
        project = create_project(
            images_kwargs=[{'name': 'image.png'}],
            files_kwargs=[{'name': 'file.pdf'}]
        )
        user = create_user(
            images_kwargs=[{'name': 'image.png'}]
        )
        self.run_cleanup_project_files(num_queries=1)
        self.run_cleanup_user_files(num_queries=1)
        # DB objects exist
        assert project.images.count() == 1
        assert project.files.count() == 1
        assert user.images.count() == 1
        # Files exist
        assert self.file_exists(project.images.first())
        assert self.file_exists(project.files.first())
        assert self.file_exists(user.images.first())

    def test_referenced_files_in_section_not_removed(self):
        with mock_time(before=timedelta(days=10)):
            project = create_project(
                report_data={'field_markdown': '![](/images/name/image.png)\n[](/files/name/file.pdf)'},
                images_kwargs=[{'name': 'image.png'}],
                files_kwargs=[{'name': 'file.pdf'}]
            )
        self.run_cleanup_project_files(num_queries=1 + 4)
        assert project.images.count() == 1
        assert project.files.count() == 1
    
    def test_referenced_files_in_finding_not_removed(self):
        with mock_time(before=timedelta(days=10)):
            project = create_project(
                findings_kwargs=[{'data': {'description': '![](/images/name/image.png)\n[](/files/name/file.pdf)'}}],
                images_kwargs=[{'name': 'image.png'}],
                files_kwargs=[{'name': 'file.pdf'}]
            )
        self.run_cleanup_project_files(num_queries=1 + 4)
        assert project.images.count() == 1
        assert project.files.count() == 1

    def test_referenced_files_in_notes_not_removed(self):
        with mock_time(before=timedelta(days=10)):
            project = create_project(
                notes_kwargs=[{'text': '![](/images/name/image.png)\n[](/files/name/file.pdf)'}],
                images_kwargs=[{'name': 'image.png'}],
                files_kwargs=[{'name': 'file.pdf'}]
            )
        self.run_cleanup_project_files(num_queries=1 + 4)
        assert project.images.count() == 1
        assert project.files.count() == 1

    def test_referenced_files_in_user_notes_not_removed(self):
        with mock_time(before=timedelta(days=10)):
            user = create_user(
                notes_kwargs=[{'text': '![](/images/name/image.png)'}],
                images_kwargs=[{'name': 'image.png'}],
            )
        self.run_cleanup_user_files(num_queries=1 + 2)
        assert user.images.count() == 1

    def test_file_referenced_by_multiple_projects(self):
        with mock_time(before=timedelta(days=10)):
            project_unreferenced = create_project(
                images_kwargs=[{'name': 'image.png'}],
                files_kwargs=[{'name': 'file.pdf'}]
            )
            project_referenced = project_unreferenced.copy()
            project_referenced.update_data({'field_markdown': '![](/images/name/image.png)\n[](/files/name/file.pdf)'})
            project_referenced.save()
        self.run_cleanup_project_files(num_queries=1 + 4 + 2 * 2 + 2 * 1)

        # Files deleted for unreferenced project
        assert project_unreferenced.images.count() == 0
        assert project_unreferenced.files.count() == 0
        # Files not deleted for referenced project
        assert project_referenced.images.count() == 1
        assert project_referenced.files.count() == 1
        # Files still present on filesystem
        assert self.file_exists(project_referenced.images.first())
        assert self.file_exists(project_referenced.files.first())

    def test_optimized_cleanup(self):
        with mock_time(before=timedelta(days=20)):
            project_old = create_project(
                images_kwargs=[{'name': 'image.png'}],
                files_kwargs=[{'name': 'file.pdf'}]
            )
            user_old = create_user(
                images_kwargs=[{'name': 'image.png'}],
            )
            project_new = create_project(
                images_kwargs=[{'name': 'image.png'}],
                files_kwargs=[{'name': 'file.pdf'}]
            )
            user_new = create_user(
                images_kwargs=[{'name': 'image.png'}],
            )
        with mock_time(before=timedelta(days=10)):
            project_new.save()
            user_new.notes.first().save()
        last_task_run = timezone.now() - timedelta(days=15)
        self.run_cleanup_project_files(num_queries=1 + 4 + 2 * 2 + 2 * 1, last_success=last_task_run)
        self.run_cleanup_user_files(num_queries=1 + 2 + 2 * 1 + 1 * 1, last_success=last_task_run)

        # Old project should be ignored because it was already cleaned in the last run
        assert project_old.images.count() == 1
        assert project_old.files.count() == 1
        assert user_old.images.count() == 1
        # New project should be cleaned because it was modified after the last run
        assert project_new.images.count() == 0
        assert project_new.files.count() == 0
        assert user_new.images.count() == 0


@pytest.mark.django_db
class TestResetStaleArchiveRestore:
    def test_reset_stale(self):
        with mock_time(before=timedelta(days=10)):
            archive = create_archived_project(project=create_project(members=[create_user(public_key=True) for _ in range(2)]))
            keypart = archive.key_parts.first()
            keypart.decrypted_at = timezone.now()
            keypart.key_part = {'key_id': 'shamir-key-id', 'key': 'dummy-key'}
            keypart.save()

        reset_stale_archive_restores(None)

        keypart.refresh_from_db()
        assert not keypart.is_decrypted
        assert keypart.decrypted_at is None
        assert keypart.key_part is None

    def test_reset_not_stale(self):
        with mock_time(before=timedelta(days=10)):
            archive = create_archived_project(project=create_project(members=[create_user(public_key=True) for _ in range(3)]))
            keypart1 = archive.key_parts.first()
            keypart1.decrypted_at = timezone.now()
            keypart1.key_part = {'key_id': 'shamir-key-id', 'key': 'dummy-key'}
            keypart1.save()
        
        keypart2 = archive.key_parts.exclude(pk=keypart1.pk).first()
        keypart2.decrypted_at = timezone.now()
        keypart2.key_part = {'key_id': 'shamir-key-id-2', 'key': 'dummy-key2'}
        keypart2.save()
        
        reset_stale_archive_restores(None)

        keypart1.refresh_from_db()
        assert keypart1.is_decrypted
        assert keypart1.decrypted_at is not None
        assert keypart1.key_part is not None
        keypart2.refresh_from_db()
        assert keypart2.is_decrypted
        assert keypart2.decrypted_at is not None
        assert keypart2.key_part is not None

    def test_reset_one_but_not_other(self):
        with mock_time(before=timedelta(days=10)):
            keypart1 = create_archived_project(project=create_project(members=[create_user(public_key=True) for _ in range(2)])).key_parts.first()
            keypart1.decrypted_at = timezone.now()
            keypart1.key_part = {'key_id': 'shamir-key-id', 'key': 'dummy-key'}
            keypart1.save()
        
        keypart2 = create_archived_project(project=create_project(members=[create_user(public_key=True) for _ in range(2)])).key_parts.first()
        keypart2.decrypted_at = timezone.now()
        keypart2.key_part = {'key_id': 'shamir-key-id', 'key': 'dummy-key'}
        keypart2.save()

        reset_stale_archive_restores(None)

        keypart1.refresh_from_db()
        assert not keypart1.is_decrypted
        keypart2.refresh_from_db()
        assert keypart2.is_decrypted


@pytest.mark.django_db
class TestAutoProjectArchiving:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user(public_key=True)
        self.project = create_project(readonly=True, members=[self.user])

        with override_settings(
            AUTOMATICALLY_ARCHIVE_PROJECTS_AFTER=timedelta(days=30),
            ARCHIVING_THRESHOLD=1,
        ):
            yield
    
    def test_archived(self):
        project_active = create_project(readonly=False, members=[self.user])

        with mock_time(after=timedelta(days=40)):
            async_to_sync(automatically_archive_projects)(None)
            assert ArchivedProject.objects.filter(name=self.project.name).exists()
            assert not PentestProject.objects.filter(id=self.project.id).exists()
            assert PentestProject.objects.filter(id=project_active.id).exists()     

    @override_settings(AUTOMATICALLY_ARCHIVE_PROJECTS_AFTER=None)
    def test_auto_archiving_disabled(self):
        with mock_time(after=timedelta(days=60)):
            async_to_sync(automatically_archive_projects)(None)
            assert PentestProject.objects.filter(id=self.project.id).exists()

    def test_project_below_auto_archive_time(self):
        with mock_time(after=timedelta(days=10)):
            async_to_sync(automatically_archive_projects)(None)
            assert PentestProject.objects.filter(id=self.project.id).exists()

    def test_counter_reset_on_unfinished(self):
        with mock_time(after=timedelta(days=20)):
            self.project.readonly = False
            self.project.save()
        with mock_time(after=timedelta(days=21)):
            self.project.readonly = True
            self.project.save()
        with mock_time(after=timedelta(days=40)):
            async_to_sync(automatically_archive_projects)(None)
            assert PentestProject.objects.filter(id=self.project.id).exists()
        with mock_time(after=timedelta(days=60)):
            async_to_sync(automatically_archive_projects)(None)
            assert ArchivedProject.objects.filter(name=self.project.name).exists()
            assert not PentestProject.objects.filter(id=self.project.id).exists()


@pytest.mark.django_db
class TestAutoArchiveDeletion:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.archive = create_archived_project()

        with override_settings(AUTOMATICALLY_DELETE_ARCHIVED_PROJECTS_AFTER=timedelta(days=30)):
            yield
    
    def test_delete(self):
        with mock_time(after=timedelta(days=60)):
            async_to_sync(automatically_delete_archived_projects)(None)
            assert not ArchivedProject.objects.filter(id=self.archive.id).exists()
    
    def test_archive_blow_time(self):
        with mock_time(after=timedelta(days=20)):
            async_to_sync(automatically_delete_archived_projects)(None)
            assert ArchivedProject.objects.filter(id=self.archive.id).exists()
    
    @override_settings(AUTOMATICALLY_DELETE_ARCHIVED_PROJECTS_AFTER=None)
    def test_auto_archive_disabled(self):
        with mock_time(after=timedelta(days=60)):
            async_to_sync(automatically_delete_archived_projects)(None)
            assert ArchivedProject.objects.filter(id=self.archive.id).exists()

