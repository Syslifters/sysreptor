import json
import logging
import sys
from unittest import mock

from weasyprint import HTML, default_url_fetcher
from weasyprint.logger import LOGGER as WEASYPRINT_LOGGER
from weasyprint.text.fonts import FontConfiguration

from .error_messages import ErrorMessage, MessageLevel
from .render_utils import FAKE_BASE_URL, RenderStageResult, request_handler


def weasyprint_render_to_pdf_sync(html_content: str, resources: dict[str, str], data: dict) -> RenderStageResult:
    out = RenderStageResult()

    def weasyprint_request_handler(url, timeout=10, ssl_context=None):
        # allow data URLs
        if url.startswith('data:'):
            return default_url_fetcher(url=url, timeout=timeout, ssl_context=ssl_context)
        return request_handler(url=url, resources=resources, messages=out.messages, data=data)

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

        out.messages.append(ErrorMessage(
            level=message_level,
            message=message_text,
            details=details_text,
        ))

    def weasyprint_strip_pdf_metadata(doc, pdf):
        # remove Producer meta-data info from PDF
        del pdf.info['Producer']

    # Capture weasyprint logs and provide as messages
    with mock.patch.object(WEASYPRINT_LOGGER, 'error', new=weasyprint_capture_logs, spec=True), \
         mock.patch.object(WEASYPRINT_LOGGER, 'warning', new=weasyprint_capture_logs, spec=True), \
         mock.patch.object(WEASYPRINT_LOGGER, 'info', new=weasyprint_capture_logs, spec=True), \
         mock.patch.object(WEASYPRINT_LOGGER, 'debug', new=weasyprint_capture_logs, spec=True):
        try:
            font_config = FontConfiguration()
            html = HTML(string=html_content, base_url=FAKE_BASE_URL, url_fetcher=weasyprint_request_handler)
            out.pdf = html.write_pdf(
                font_config=font_config,
                presentational_hints=True,
                optimize_images=False,
                uncompressed_pdf=False,
                finisher=weasyprint_strip_pdf_metadata,
            )
        except Exception:
            logging.exception('Error rendering PDF (stage: weasyprint)')
            out.messages.append(ErrorMessage(
                level=MessageLevel.ERROR,
                message='Error rendering PDF (stage: weasyprint)',
            ))

    return out


def main():
    kwargs = json.loads(sys.stdin.read())
    res = weasyprint_render_to_pdf_sync(**kwargs)
    print(json.dumps(res.to_dict(include_other=True)))  # noqa: T201


if __name__ == '__main__':
    main()
