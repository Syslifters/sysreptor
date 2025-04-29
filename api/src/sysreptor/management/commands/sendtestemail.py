
from asgiref.sync import async_to_sync
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from sysreptor.utils import mail


class Command(BaseCommand):
    help = 'Test that the email settings are correct by sending a test email.'

    def add_arguments(self, parser):
        parser.add_argument('recipient', help='Recipient of the test email')

    def handle(self, recipient, **options):
        if not settings.EMAIL_HOST:
            raise CommandError('EMAIL_HOST is not configured')

        async_to_sync(mail.send_mail)(
            to=recipient,
            subject='SysReptor Test Email',
            template_name='email/test.html',
            template_context={},
        )

        self.stdout.write(self.style.SUCCESS(f'Successfully sent test email to "{recipient}".'))
