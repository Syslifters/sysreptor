import os

from django.contrib.auth.management.commands import createsuperuser
from django.core.management import CommandError


class Command(createsuperuser.Command):
    help = 'Create a superuser, or update the password for an existing superuser.'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--password', dest='password', default=None,
            help='Specifies the password for the superuser.',
        )

    def handle(self, *args, **options):
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        username = options.get('username')
        database = options.get('database')

        if not password or not username:
            raise CommandError("username and password (DJANGO_SUPERUSER_PASSWORD) must be set")
        if len(password) < 15:
            raise CommandError("password must be at least 15 characters")

        exists = self.UserModel._default_manager.db_manager(database).filter(username=username).exists()
        if exists:
            user = self.UserModel._default_manager.db_manager(database).filter(username=username).first()
            user.set_password(password)
            user.save()
            self.stdout.write("User exists, updated password.")
            return

        super(Command, self).handle(*args, **options)
