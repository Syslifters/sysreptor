import json
import logging
from contextlib import asynccontextmanager
from html import escape as html_escape

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from playwright.async_api import async_playwright
from weasyprint.urls import URLFetchingError

from reportcreator_api.utils.logging import log_timing

from .error_messages import ErrorMessage, MessageLevel
from .render_utils import FAKE_BASE_URL, RenderStageResult, request_handler


@asynccontextmanager
async def get_page():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            executable_path=settings.CHROMIUM_EXECUTABLE,
            headless=True,
            chromium_sandbox=False,
            handle_sigint=False,
            handle_sigterm=False,
            handle_sighup=False,
        )
        context = await browser.new_context(
            base_url=FAKE_BASE_URL,
            offline=True,
            java_script_enabled=True,
            service_workers='block',
            accept_downloads=False,
        )
        yield await context.new_page()


def get_render_script():
    return (settings.PDF_RENDER_SCRIPT_PATH).read_text()


@log_timing(log_start=True)
async def chromium_render_to_html(template: str, styles: str, resources: dict[str, str], data: dict, language: str) -> RenderStageResult:
    out = RenderStageResult()

    async def chromium_request_handler(route):
        # Prevent loading images and media to speed up template rendering.
        # Only weasyprint needs them for PDF rendering
        if route.request.resource_type in ['image', 'media']:
            await route.abort()
            return

        try:
            fileinfo = request_handler(url=route.request.url, resources=resources, messages=out.messages, data=data)
            await route.fulfill(body=fileinfo['file_obj'].read())
        except URLFetchingError:
            await route.abort()

    try:
        chromium_startup_timer = out.add_timing('chromium_startup')
        chromium_startup_timer.__enter__()
        async with get_page() as page:
            chromium_startup_timer.__exit__(None, None, None)

            with out.add_timing('chromium_rendering'):
                console_output = []
                page.on('console', lambda l: console_output.append(l))
                page.on('pageerror', lambda exc: out.messages.add(ErrorMessage(
                    level=MessageLevel.ERROR,
                    message='Uncaught error during template rendering',
                    details=str(exc),
                )))

                # Catch all requests
                await page.route('**/*', chromium_request_handler)

                # Load Vue template
                await page.route(FAKE_BASE_URL + '/', lambda route: route.fulfill(content_type='text/html', body=''))
                await page.goto(FAKE_BASE_URL)
                await page.set_content(f"""
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
                await page.evaluate(f"""() => {{
                    window.REPORT_TEMPLATE = {json.dumps(template, cls=DjangoJSONEncoder)};
                    window.REPORT_DATA = {json.dumps(data, cls=DjangoJSONEncoder)};
                }}""")

                if styles:
                    await page.add_style_tag(content=styles)
                await page.add_script_tag(content=get_render_script())

                # Wait for template to finish rendering
                await page.wait_for_function("""window.RENDERING_COMPLETED === true""")

                # Format messages
                for m in console_output:
                    msg = {
                        'level': m.type,
                        'message': m.text,
                        'details': None,
                        'location': None,
                    }
                    if len(m.args) == 2 and (error_data := await m.args[1].json_value()) and 'message' in error_data:
                        msg |= {
                            'message': str(error_data['message']),
                            'details': str(error_data['details']) if error_data.get('details') else None,
                        }
                    if msg['message'] in [
                        '[Vue warn]: Avoid app logic that relies on enumerating keys on a component instance. The keys will be empty in production mode to avoid performance overhead.',
                    ] or msg['message'].startswith('Failed to load resource: net::'):
                        continue
                    if msg['level'] not in ['error', 'warning', 'info']:
                        msg['level'] = 'info'
                    out.messages.append(ErrorMessage(**msg | {'level': MessageLevel(msg['level'])}))

                if not any(map(lambda m: m.level == MessageLevel.ERROR, out.messages)):
                    # Remove script tag from HTML output
                    await page.evaluate("""() => document.head.querySelectorAll('script').forEach(s => s.remove())""")
                    # Get rendered HTML
                    html = await page.content()
                    # Post-process HTML
                    out.pdf = html.replace('data-checked="checked"', 'checked').encode()
    except Exception:
        out.messages.append(ErrorMessage(
            level=MessageLevel.ERROR,
            message='Error rendering HTML template',
        ))

    if out.messages:
        logging.info(f'Chromium messages: {out.messages}')

    return out
