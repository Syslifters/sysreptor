import json
import logging
import re
from base64 import b64decode
from contextlib import contextmanager
from html import escape as html_escape
from io import BytesIO
from pathlib import Path
from typing import Optional
from unittest import mock

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from pikepdf import Encryption, Pdf
from playwright.sync_api import sync_playwright
from weasyprint import HTML, default_url_fetcher
from weasyprint.logger import LOGGER as WEASYPRINT_LOGGER
from weasyprint.text.fonts import FontConfiguration
from weasyprint.urls import URLFetchingError

from reportcreator_api.utils.error_messages import ErrorMessage, MessageLevel, MessageLocationInfo, MessageLocationType
from reportcreator_api.utils.logging import log_timing

# Base URL prefix for PDF rendering. Is never actually called
FAKE_BASE_URL = 'https://pdf.sysreptor.com'


def get_location_info(content: str, objs: list[dict], type: MessageLocationType, get_name=None) -> Optional[MessageLocationInfo]:
    def check_field(val, path, **kwargs):
        if isinstance(val, dict):
            return check_obj(val, path, **kwargs)
        elif isinstance(val, list):
            for idx, item in enumerate(val):
                if res := check_field(val=item, path=path + [f'[{idx}]'], **kwargs):
                    return res
        elif isinstance(val, str):
            if content in val:
                return MessageLocationInfo(type=type, **kwargs).for_path(path)

    def check_obj(obj, path, **kwargs):
        for k, v in obj.items():
            if res := check_field(val=v, path=path + [k], **kwargs):
                return res

    for o in objs:
        if res := check_field(val=o, path=[], id=o.get('id'), name=get_name(o) if get_name else None):
            return res


def request_handler(url, resources: dict[str, str], messages: set[ErrorMessage], data: dict) -> dict:
    if url.startswith(FAKE_BASE_URL):
        url = url[len(FAKE_BASE_URL):]

    # allow loading from the resource list
    if url in resources:
        return {
            'filename': url.split('/')[-1],
            'file_obj': BytesIO(b64decode(resources[url])),
        }
    elif (m := re.fullmatch(r'^/assets/global/([a-z0-9-_.]+)$', url)) and (global_asset := Path(__file__).parent / 'global_assets' / m.group(1)) and global_asset.exists():
        return {
            'filename': global_asset.name,
            'file_obj': global_asset.open('rb'),
        }
    elif url.startswith('/'):
        messages.add(ErrorMessage(
            level=MessageLevel.WARNING,
            message='Resource not found',
            details=f'Could not find resource for URL "{url}". Check if the URL is correct and the resource exists on the server.',
            location=get_location_info(content=url, objs=data.get('findings', []), type=MessageLocationType.FINDING, get_name=lambda f: f.get('title')) or
                     get_location_info(content=url, objs=data.get('sections', {}).values(), type=MessageLocationType.SECTION, get_name=lambda s: s.get('label')) or
                     None,
        ))
        raise URLFetchingError('Resource not found')
    else:
        # block all external requests
        messages.add(ErrorMessage(
            level=MessageLevel.WARNING,
            message='Blocked request to external URL',
            details=f'Block request to URL "{url}". Requests to external systems are forbidden for security reasons.\nUpload this resource as assset and include it via its asset URL.',
        ))
        raise URLFetchingError('External requests not allowed')


@contextmanager
def get_page():
    with sync_playwright() as playwright:
        with playwright.chromium.launch(
            executable_path=settings.CHROMIUM_EXECUTABLE,
            headless=True,
            chromium_sandbox=False,
            handle_sigint=False,
            handle_sigterm=False,
            handle_sighup=False
        ) as browser:
            with browser.new_context(
                base_url=FAKE_BASE_URL,
                offline=False,  # Offline mode prevents request mocking. A catch-all route handler is used instead
                java_script_enabled=True,
                service_workers='block',
                accept_downloads=False,
            ) as context:
                yield context.new_page()


def get_render_script():
    return (settings.PDF_RENDER_SCRIPT_PATH).read_text()


@log_timing
def render_to_html(template: str, styles: str, resources: dict[str, str], data: dict, language: str) -> tuple[Optional[str], set[ErrorMessage]]:
    messages = set()
    html = None

    def chromium_request_handler(route):
        # Prevent loading images and media to speed up template rendering.
        # Only weasyprint needs them for PDF rendering
        if route.request.resource_type in ['image', 'media']:
            route.abort()
            return

        try:
            fileinfo = request_handler(url=route.request.url, resources=resources, messages=messages, data=data)
            route.fulfill(body=fileinfo['file_obj'].read())
        except URLFetchingError:
            route.abort()

    try:
        with get_page() as page:
            console_output = []
            page.on('console', lambda l: console_output.append(l))
            page.on('pageerror', lambda exc: messages.add(ErrorMessage(
                level=MessageLevel.ERROR,
                message='Uncaught error during template rendering',
                details=str(exc)
            )))

            # Catch all requests
            page.route('**', chromium_request_handler)

            # Load Vue template
            page.route(FAKE_BASE_URL + '/', lambda route: route.fulfill(content_type='text/html', body=''))
            page.goto(FAKE_BASE_URL)
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

            if styles:
                page.add_style_tag(content=styles)
            page.add_script_tag(content=get_render_script())

            # Wait for template to finish rendering
            page.wait_for_function("""window.RENDERING_COMPLETED === true""")

            # Format messages
            for m in console_output:
                msg = {
                    'level': m.type,
                    'message': m.text,
                    'details': None,
                    'location': None,
                }
                if len(m.args) == 2 and (error_data := m.args[1].json_value()) and 'message' in error_data:
                    msg |= {
                        'message': str(error_data['message']),
                        'details': str(error_data['details']) if error_data.get('details') else None,
                    }
                if msg['message'] in [
                    '[Vue warn]: Avoid app logic that relies on enumerating keys on a component instance. The keys will be empty in production mode to avoid performance overhead.',
                    'Failed to load resource: net::ERR_FAILED',
                ]:
                    continue
                if msg['level'] not in ['error', 'warning', 'info']:
                    msg['level'] = 'info'
                messages.add(ErrorMessage(**msg | {'level': MessageLevel(msg['level'])}))

            if not any(map(lambda m: m.level == MessageLevel.ERROR, messages)):
                # Remove script tag from HTML output
                page.evaluate("""() => document.head.querySelectorAll('script').forEach(s => s.remove())""")
                # Get rendered HTML
                html = page.content()
    except Exception:
        messages.add(ErrorMessage(
            level=MessageLevel.ERROR,
            message='Error rendering HTML template',
        ))

    if messages:
        logging.info(f'Chromium messages: {messages}')

    return html, messages


def weasyprint_strip_pdf_metadata(doc, pdf):
    # remove Producer meta-data info from PDF
    del pdf.info['Producer']


@log_timing
def render_to_pdf(html_content: str, resources: dict[str, str], data: dict) -> tuple[Optional[bytes], set[ErrorMessage]]:
    messages = set()

    def weasyprint_request_handler(url, timeout=10, ssl_context=None):
        # allow data URLs
        if url.startswith('data:'):
            return default_url_fetcher(url=url, timeout=timeout, ssl_context=ssl_context)
        return request_handler(url=url, resources=resources, messages=messages, data=data)

    def weasyprint_capture_logs(msg, *args, **kwargs):
        ignore_messages = [
            # Loading errors are already handled by the weasyprint URL fetcher
            'Failed to load image at',
            'Failed to load inline SVG:',
            'Failed to load stylesheet at',
            'Failed to load attachment:',
            # Suppress message for unsupported "overflow-x" rule use by highlight.js markdown code block syntax highlighting
            'Ignored `overflow-x:',
        ]
        html_messages = [
            'Invalid date in <meta name="',
            'Anchor defined twice:',
            'This table row has more columns than the table, ignored',
            'Unsupported stylesheet type',
            'Missing href in <link rel="attachment">',
            'No anchor #%s for internal URI reference',
            'Relative URI reference without a base URI:',
        ]
        font_messages = [
            'Failed to get matching local font for',
            'Failed to load local font',
            'Failed to load font at',
            'Failed to handle woff font at',
        ]
        message_level = MessageLevel.WARNING
        message_text = 'Invalid CSS'
        details_text = msg % (args or kwargs)

        if any(map(lambda m: details_text.startswith(m), ignore_messages)):
            return
        elif any(map(lambda m: msg.startswith(m), html_messages)):
            message_text = 'Invalid HTML'
        elif any(map(lambda m: msg.startswith(m), font_messages)):
            message_text = 'Font loading problem'
            message_level = MessageLevel.INFO

        messages.add(ErrorMessage(
            level=message_level,
            message=message_text,
            details=details_text,
        ))

    # Capture weasyprint logs and provide as messages
    res = None
    with mock.patch.object(WEASYPRINT_LOGGER, 'error', new=weasyprint_capture_logs, spec=True), \
         mock.patch.object(WEASYPRINT_LOGGER, 'warning', new=weasyprint_capture_logs, spec=True), \
         mock.patch.object(WEASYPRINT_LOGGER, 'info', new=weasyprint_capture_logs, spec=True), \
         mock.patch.object(WEASYPRINT_LOGGER, 'debug', new=weasyprint_capture_logs, spec=True):
        try:
            font_config = FontConfiguration()
            html = HTML(string=html_content, base_url=FAKE_BASE_URL, url_fetcher=weasyprint_request_handler)
            res = html.write_pdf(
                font_config=font_config,
                presentational_hints=True,
                optimize_images=False,
                finisher=weasyprint_strip_pdf_metadata
            )
        except Exception:
            logging.exception('Error rendering PDF')
            messages.add(ErrorMessage(
                level=MessageLevel.ERROR,
                message='Error rendering PDF'
            ))

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


def render_pdf(template: str, styles: str, data: dict, resources: dict, language: str, password: Optional[str] = None, output=None) -> tuple[Optional[bytes], set[ErrorMessage]]:
    msgs = set()
    html, html_msgs = render_to_html(
        template=template,
        styles=styles,
        resources=resources,
        data=data,
        language=language,
    )
    msgs |= html_msgs
    if html is None:
        return html, msgs
    elif output == 'html':
        return html.encode(), msgs

    pdf, pdf_msgs = render_to_pdf(
        html_content=html,
        resources=resources,
        data=data
    )
    msgs |= pdf_msgs
    if pdf is None:
        return pdf, msgs

    pdf_enc = encrypt_pdf(
        pdf_data=pdf,
        password=password
    )
    return pdf_enc, msgs

