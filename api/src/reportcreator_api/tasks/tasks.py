from datetime import timedelta

from django.core.management import call_command

from reportcreator_api.tasks.models import periodic_task


@periodic_task(id='clear_sessions', schedule=timedelta(days=1))
def clear_sessions(task_info):
    call_command('clearsessions')
