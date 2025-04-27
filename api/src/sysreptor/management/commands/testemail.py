import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

from sysreptor.utils.mail import html_to_text


class Command(BaseCommand):
    help = 'Test that the email settings are correct by receiving a dummy email.'

    def add_arguments(self, parser):
        parser.add_argument('--recipient', help='Recipient of the test email')

    def send_mail(self, to: str|list[str], subject: str, template_name: str, template_context: dict):
        if not settings.EMAIL_HOST or not to:
            return

        body_html = render_to_string(template_name=template_name, context=template_context)
        body_text = html_to_text(body_html)

        mail = EmailMultiAlternatives(
            to=[to] if isinstance(to, str) else to,
            from_email=settings.DEFAULT_FROM_EMAIL,
            headers={
                'From': f'SysReptor <{settings.DEFAULT_FROM_EMAIL}>',
            },
            subject=subject,
            body=body_text,
        )
        mail.attach_alternative(body_html, 'text/html')
        mail.send()

    def handle(self, recipient, **options):
        if not settings.EMAIL_HOST:
            raise ImproperlyConfigured('EMAIL_HOST not set')

        self.send_mail(
            to=recipient,
            subject='SysReptor Test Email',
            template_name='email/forgot_password.html',
            template_context={
                'user': "user",
                'confirmation_link': "test_email",
                'confirmation_link_valid_hours': settings.PASSWORD_RESET_TIMEOUT // 3600,
            },
        )

        logging.info(f'Email sent succesfully to "{recipient}".')