from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from lxml import etree

from sysreptor.conf.taskiq import background_task


def is_email_configured() -> bool:
    return bool(settings.MAILERS.get('default', {}))


def get_default_from_email() -> str:
    if not is_email_configured():
        return ''
    return settings.MAILERS.get('default', {}).get('FROM_EMAIL', '')


def html_to_text(html):
    document = etree.HTML(html)
    el = document.find(".//*[@id='content']")
    lines = list(map(str.strip, el.itertext()))
    lines_cleaned = []
    for l in lines:
        if l or (not l and lines_cleaned and lines_cleaned[-1]):
            lines_cleaned.append(l)
    return '\n'.join(lines_cleaned)


@background_task('send_mail')
@sync_to_async(thread_sensitive=False)
def send_mail(to: str|list[str], subject: str, template_name: str, template_context: dict):
    if not is_email_configured() or not to:
        return

    from_email = get_default_from_email()
    body_html = render_to_string(template_name=template_name, context=template_context)
    body_text = html_to_text(body_html)

    mail = EmailMultiAlternatives(
        to=[to] if isinstance(to, str) else to,
        from_email=from_email,
        headers={
            'From': f'SysReptor <{from_email}>',
        },
        subject=subject,
        body=body_text,
    )
    mail.attach_alternative(body_html, 'text/html')
    mail.send()
