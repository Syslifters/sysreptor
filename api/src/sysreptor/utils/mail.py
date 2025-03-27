from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from lxml import etree

from sysreptor.utils.utils import run_in_background


def html_to_text(html):
    document = etree.HTML(html)
    el = document.find(".//*[@id='content']")
    lines = list(map(str.strip, el.itertext()))
    lines_cleaned = []
    for l in lines:
        if l or (not l and lines_cleaned and lines_cleaned[-1]):
            lines_cleaned.append(l)
    return '\n'.join(lines_cleaned)


@sync_to_async(thread_sensitive=False)
def send_mail(to: str|list[str], subject: str, template_name: str, template_context: dict):
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


async def send_mail_in_background(*args, **kwargs):
    run_in_background(send_mail)(*args, **kwargs)

