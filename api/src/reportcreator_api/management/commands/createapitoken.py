import uuid
from datetime import date

from django.core.management.base import BaseCommand, CommandError

from reportcreator_api.users.models import APIToken, PentestUser


class Command(BaseCommand):
    help = 'Create an API token for a user'

    def add_arguments(self, parser):
        parser.add_argument('user', default=None)
        parser.add_argument('--name', default='API Token created via CLI', help='Name of the API token')
        parser.add_argument('--expire-date', type=date.fromisoformat, default=None, help='Expiration date of the token in ISO format YYYY-MM-DD')

    def handle(self, user, name=None, expire_date=None, **options):
        user = self.get_user(user)
        token = APIToken.objects.create(
            user=user,
            name=name,
            expire_date=expire_date,
        )
        print(token.token_formatted)  # noqa: T201


    def get_user(self, u):
        try:
            return PentestUser.objects.get(id=uuid.UUID(u))
        except Exception:
            try:
                return PentestUser.objects.get(username=u)
            except PentestUser.DoesNotExist:
                raise CommandError(f'User "{u}" not found') from None
