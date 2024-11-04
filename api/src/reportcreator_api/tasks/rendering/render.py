import asyncio
import json
import logging
import sys
import tempfile
import time
from io import BytesIO
from pathlib import Path
from typing import Optional

from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from pikepdf import Encryption, Pdf

from reportcreator_api.tasks.rendering.error_messages import (
    ErrorMessage,
    MessageLevel,
)
from reportcreator_api.tasks.rendering.render_chromium import chromium_render_to_html
from reportcreator_api.tasks.rendering.render_utils import RenderStageResult
from reportcreator_api.utils.logging import log_timing


@log_timing(log_start=True)
async def weasyprint_render_to_pdf(**kwargs) -> RenderStageResult:
    weasyprint_before_process_start = time.perf_counter()

    proc = None
    try:
        # Run weasyprint in a subprocess to be able to cancel it
        proc = await asyncio.create_subprocess_exec(
            *[
                sys.executable,
                '-m',
                'rendering.render_weasyprint',
            ],
            cwd=Path(__file__).parent.parent,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate(input=json.dumps(kwargs, cls=DjangoJSONEncoder).encode())
        if proc.returncode != 0:
            raise Exception(f'weasyprint failed with return code {proc.returncode}')
        out = RenderStageResult.from_dict(json.loads(stdout.decode()))

        if weasyprint_process_started := out.other.pop('weasyprint_startup', None):
            out.timings['weasyprint_startup'] = weasyprint_process_started - weasyprint_before_process_start
        return out
    except Exception:
        return RenderStageResult(
            pdf=None,
            messages=[
                ErrorMessage(
                    level=MessageLevel.ERROR,
                    message='Error rendering PDF',
                ),
            ],
        )
    finally:
        if proc and proc.returncode is None:
            proc.kill()


@log_timing(log_start=True)
async def compress_pdf(pdf_data: bytes) -> RenderStageResult:
    out = RenderStageResult()
    proc = None
    try:
        with out.add_timing('compress_pdf'), \
             tempfile.NamedTemporaryFile() as pdfin, \
             tempfile.NamedTemporaryFile() as pdfout:
            pdfin.write(pdf_data)
            proc = await asyncio.create_subprocess_exec(*[
                settings.GHOSTSCRIPT_EXECUTABLE,
                '-sDEVICE=pdfwrite',
                '-dPDFSETTIGS=/printer',
                '-dNOPAUSE', '-dQUIET', '-dBATCH',
                f'-sOutputFile={pdfout.name}',
                pdfin.name,
            ])
            await asyncio.wait_for(proc.wait(), timeout=60)

            if proc.returncode != 0:
                raise Exception(f'Ghostscript failed with exit code {proc.returncode}')

            pdfout.seek(0)
            out.pdf = pdfout.read()
    except Exception:
        logging.exception('Error while compressing PDF')
        out.messages.append(ErrorMessage(
            level=MessageLevel.WARNING,
            message='Could not compress PDF',
        ))
    finally:
        if proc and proc.returncode is None:
            proc.kill()
    return out


@log_timing()
@sync_to_async()
def encrypt_pdf(pdf_data: bytes, password: Optional[str]) -> RenderStageResult:
    out = RenderStageResult(pdf=pdf_data)
    if not password:
        return out

    with out.add_timing('compress_pdf'), \
         Pdf.open(BytesIO(pdf_data)) as pdf:
        out_data = BytesIO()
        # Encrypt PDF with AES-256
        pdf.save(
            filename_or_stream=out_data,
            encryption=Encryption(owner=password, user=password, aes=True, R=6) if password else False,
        )
        out.pdf = out_data.getvalue()
        return out


async def render_pdf_impl(
    template: str, styles: str, data: dict, resources: dict, language: str,
    password: Optional[str] = None, should_compress_pdf: bool = False, output=None,
) -> RenderStageResult:
    out = RenderStageResult()

    out |= await chromium_render_to_html(
        template=template,
        styles=styles,
        resources=resources,
        data=data,
        language=language,
    )
    if out.pdf is None or output == 'html':
        return out

    out |= await weasyprint_render_to_pdf(
        html_content=out.pdf.decode(),
        resources=resources,
        data=data,
    )
    if out.pdf is None:
        return out

    if should_compress_pdf:
        out |= await compress_pdf(pdf_data=out.pdf)
        if out.pdf is None:
            return out

    if password:
        out |= await encrypt_pdf(
            pdf_data=out.pdf,
            password=password,
        )
    return out

