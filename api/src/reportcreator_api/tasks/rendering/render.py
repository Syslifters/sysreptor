import asyncio
import json
import logging
import sys
import tempfile
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


async def weasyprint_start_process():
    # Run weasyprint in a subprocess to be able to cancel it
    return await asyncio.create_subprocess_exec(
        *[
            sys.executable,
            '-m',
            'rendering.render_weasyprint',
        ],
        cwd=Path(__file__).parent.parent,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
    )


@log_timing(log_start=True)
async def weasyprint_render_to_pdf(proc, **kwargs) -> RenderStageResult:
    @sync_to_async
    def encode_data():
        return json.dumps(kwargs, cls=DjangoJSONEncoder).encode()

    @sync_to_async
    def decode_data(stdout):
        return RenderStageResult.from_dict(json.loads(stdout.decode()))

    try:
        out = RenderStageResult()
        with out.add_timing('weasyprint'):
            stdout, _ = await proc.communicate(input=await encode_data())
            if proc.returncode != 0:
                raise Exception(f'weasyprint failed with return code {proc.returncode}')
            res = await decode_data(stdout)
        out |= res
        return out
    except Exception:
        return RenderStageResult(
            pdf=None,
            messages=[
                ErrorMessage(
                    level=MessageLevel.ERROR,
                    message='Error rendering PDF (stage: weasyprint)',
                ),
            ],
        )


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
        logging.exception('Error while compressing PDF (ghostscript)')
        out.pdf = pdf_data
        out.messages.append(ErrorMessage(
            level=MessageLevel.WARNING,
            message='Could not compress PDF (ghostscript)',
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

    with out.add_timing('encrypt_pdf'), \
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

    # Start weasyprint subprocess in parallel with chromium rendering, because python has a long startup time
    weasyprint_proc = (await weasyprint_start_process()) if output != 'html' else None
    try:
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
            proc=weasyprint_proc,
            html_content=out.pdf.decode(),
            resources=resources,
            data=data,
        )
        if out.pdf is None:
            return out
    finally:
        if weasyprint_proc and weasyprint_proc.returncode is None:
            weasyprint_proc.kill()

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

