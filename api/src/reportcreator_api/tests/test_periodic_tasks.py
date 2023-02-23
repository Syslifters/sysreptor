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
