import json
import logging
from playwright.sync_api import sync_playwright
from typing import Optional
from base64 import b64decode
from html import escape as html_escape
from io import BytesIO
from pikepdf import Pdf, Encryption
from contextlib import contextmanager
from weasyprint import HTML, CSS, default_url_fetcher
from weasyprint.text.fonts import FontConfiguration
from weasyprint.urls import URLFetchingError
from django.core.serializers.json import DjangoJSONEncoder

from django.conf import settings
from reportcreator_api.utils.logging import log_timing


@contextmanager
def get_page():
    with sync_playwright() as playwright:
        with playwright.chromium.launch(
            executable_path=settings.CHROMIUM_EXECUTABLE,
            args=['--single-process'],
            headless=True,
            chromium_sandbox=False,
            handle_sigint=False,
            handle_sigterm=False,
            handle_sighup=False
        ) as browser:
            with browser.new_context() as context:
                yield context.new_page()


def get_render_script():
    return (settings.PDF_RENDER_SCRIPT_PATH).read_text()


@log_timing
def render_to_html(template: str, data: dict, language: str) -> tuple[Optional[str], list[dict]]:
    messages = []
    html = None

    try:
        with get_page() as page:
            console_output = []
            page.on('console', lambda l: console_output.append(l))
            page.on('pageerror', lambda exc: messages.append({'level': 'error', 'message': 'Uncaught error during template rendering', 'details': str(exc)}))
            page.on('requestfailed', lambda request: messages.append({'level': 'error', 'message': 'Request failed', 'details': f'Request to URL {request.url} failed: {request.failure.error_text}'}))
            page.set_content(f"""
                <!DOCTYPE html>
                <html lang="{html_escape(language)}">
                <head>
                    <meta charset="utf-8">
                    <title>{html_escape(data.get('title', ''))}</title>
                </head>
                <body>
                </body>
            """)

            # set global window variables
            page.evaluate(f"""() => {{
                window.REPORT_TEMPLATE = {json.dumps(template, cls=DjangoJSONEncoder)};
                window.REPORT_DATA = {json.dumps(data, cls=DjangoJSONEncoder)};
            }}""")
            
            page.add_script_tag(content=get_render_script())

            # Wait for template to finish rendering
            page.wait_for_function("""window.RENDERING_COMPLETED === true""");

            # Format messages
            for m in console_output:
                msg = {
                    'level': m.type,
                    'message': m.text,
                    'details': None
                }
                if len(m.args) == 2 and (error_data := m.args[1].json_value()) and 'message' in error_data:
                    msg |= {
                        'message': error_data['message'],
                        'details': error_data.get('details'),
                    }
                if msg['level'] in ['error', 'warning', 'info']:
                    messages.append(msg)
            
            if not any(map(lambda m: m['level'] == 'error', messages)):
                # Remove script tag from HTML output
                page.evaluate("""() => document.head.querySelectorAll('script').forEach(s => s.remove())""")
                # Get rendered HTML
                html = page.content()
    except Exception as ex:
        messages.append({
            'level': 'error',
            'message': 'Error rendering HTML template',
            'details': None,
        })

    if messages:
        logging.info(f'Chromium messages: {messages}')

    return html, messages


def weasyprint_strip_pdf_metadata(doc, pdf):
    # remove Producer meta-data info from PDF
    del pdf.info['Producer']


@log_timing
def render_to_pdf(html_content: str, css_styles: str, resources: dict[str, str]) -> tuple[Optional[bytes], list[dict]]:
    messages = []

    def weasyprint_url_fetcher(url, timeout=10, ssl_context=None):
        # allow data URLs
        if url.startswith('data:'):
            return default_url_fetcher(url=url, timeout=timeout, ssl_context=ssl_context)
        # allow loading from the resource list
        elif url in resources:
            return {
                'filename': url.split('/')[-1],
                'file_obj': BytesIO(b64decode(resources[url])),
            }
        elif url.startswith('/'):
            messages.append({
                'level': 'error',
                'message': 'Resource not found',
                'details': f'Could not find resource for URL "{url}". Check if the URL is correct and the resource exists on the server.',
            })
            raise URLFetchingError('Resource not found')
        else:
            # block all external requests
            messages.append({
                'level': 'error',
                'message': 'Blocked request to external URL',
                'details': f'Block request to URL "{url}". Requests to external systems are forbidden for security reasons.\nUpload this resource as assset and include it via its asset URL.',
            })
            raise URLFetchingError('External requests not allowed')

    font_config = FontConfiguration()
    html = HTML(string=html_content, base_url='reportcreator://', url_fetcher=weasyprint_url_fetcher)
    css = CSS(string=css_styles, font_config=font_config, base_url='reportcreator://', url_fetcher=weasyprint_url_fetcher)
    rendered = html.render(stylesheets=[css], font_config=font_config, optimize_size=[], presentational_hints=True)

    res = None
    if not any(map(lambda m: m['level'] == 'error', messages)):
        res = rendered.write_pdf(finisher=weasyprint_strip_pdf_metadata)
    return res, messages


@log_timing
def encrypt_pdf(pdf_data: bytes, password: Optional[str]) -> bytes:
    if not password:
        return pdf_data

    with Pdf.open(BytesIO(pdf_data)) as pdf:
        out = BytesIO()
        # Encrypt PDF with AES-256
        pdf.save(
            filename_or_stream=out, 
            encryption=Encryption(owner=password, user=password, aes=True, R=6) if password else False,
            compress_streams=True
        )
        return out.getvalue()


def render_pdf(template: str, styles: str, data: dict, resources: dict, language: str, password: Optional[str] = None) -> tuple[Optional[bytes], list[dict]]:
    msgs = []
    html, html_msgs = render_to_html(
        template=template,
        data=data,
        language=language,
    )
    msgs += html_msgs
    if html is None:
        return None, msgs
    
    pdf, pdf_msgs = render_to_pdf(
        html_content=html,
        css_styles=styles,
        resources=resources,
    )
    msgs += pdf_msgs
    if pdf is None:
        return None, msgs

    pdf_enc = encrypt_pdf(
        pdf_data=pdf, 
        password=password
    )
    return pdf_enc, msgs
