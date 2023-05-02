

import argparse
import shutil
import tempfile
import uuid
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from reportcreator_api.pentests.models.project import PentestProject

from reportcreator_api.users.models import PentestUser
from reportcreator_api.archive.import_export import import_project_types, import_templates, import_projects


class Command(BaseCommand):
    help = 'Import archives containing demo data'

    def add_arguments(self, parser):
        parser.add_argument('file', nargs='?', type=argparse.FileType('rb'), default='-')
        parser.add_argument('--type', choices=['design', 'template', 'project'])
        parser.add_argument('--add-member', action='append', help='Add user as member to imported projects')

    def get_user(self, u):
        try:
            return PentestUser.objects.get(id=uuid.UUID(u))
        except Exception:
            pass
        try:
            return PentestUser.objects.get(username=u)
        except PentestUser.DoesNotExist:
            raise CommandError(f'User "{u}" not found')

    def handle(self, file, type, add_member, *args, **options):
        if type == 'project':
            add_member = list(map(self.get_user, add_member))
        
        import_func = {
            'design': import_project_types,
            'template': import_templates,
            'project': import_projects,
        }[type]

        with tempfile.SpooledTemporaryFile(max_size=settings.FILE_UPLOAD_MAX_MEMORY_SIZE, mode='w+b') as f:
            shutil.copyfileobj(file, f)
            f.seek(0)
            imported = import_func(f)
        if type == 'project':
            for u in add_member:
                PentestProject.objects.add_member(u, imported)

