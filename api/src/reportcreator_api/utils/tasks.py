from django.core.management import call_command


def clear_sessions(task_info):
    call_command('clearsessions')

