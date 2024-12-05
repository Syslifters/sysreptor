from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from ...models import ProjectNumber


class Command(BaseCommand):
    help = 'Reset the project number counter'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('value', nargs='?', type=int, default=0, help='New project number counter value')

    def handle(self, *args: Any, value=0, **options: Any) -> str | None:
        if value < 0:
            raise CommandError('Project number counter must be a non-negative integer')
        
        counter, _ = ProjectNumber.objects.update_or_create(
            pk=1,
            defaults={'current_id': value},
            create_defaults={'current_id': value},
        )
        print(f'Project number was reset to {counter.current_id}')
