from pathlib import Path

import zipstream
from django.db.models import Prefetch, prefetch_related_objects
from django.utils.crypto import get_random_string
from rest_framework.generics import GenericAPIView
from rest_framework.serializers import Serializer
from rest_framework.settings import api_settings
from sysreptor.api_utils.backup_utils import to_chunks
from sysreptor.pentests.models import ProjectMemberInfo
from sysreptor.pentests.views import ProjectSubresourceMixin
from sysreptor.utils.api import StreamingHttpResponseAsync

from .md_format import format_project


def file_chunks(f):
    with f.open() as fp:
        yield from fp.chunks()


def safe_zip_name(name: str) -> str:
    base = Path(name.replace('\\', '/') or "").name
    if base in {"", ".", ".."}:
        base = f"file-{get_random_string(8)}"
    return base


class MarkdownExportView(ProjectSubresourceMixin, GenericAPIView):
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES
    serializer_class = Serializer

    def get(self, request, *args, **kwargs):
        project = self.get_project()
        prefetch_related_objects(
            [project], 
            'findings', 'sections', 'notes', 'images', 'files',
            Prefetch('members', queryset=ProjectMemberInfo.objects.select_related('user')),
        )

        md = format_project(project)
        z = zipstream.ZipStream(compress_type=zipstream.ZIP_DEFLATED)
        for f in project.images.all():
            if project.is_file_referenced(f, sections=True, findings=True, notes=False):
                f_name = safe_zip_name(f.name)
                md = md.replace(f'/images/name/{f.name}', 'assets/' + f_name)
                z.add(arcname=str(Path('assets') / f_name), data=file_chunks(f.file))
        for f in project.project_type.assets.all():
            if project.is_file_referenced(f, sections=True, findings=True, notes=False):
                f_name = safe_zip_name(f.name)
                md = md.replace(f'/assets/name/{f.name}', 'assets/' + f_name)
                z.add(arcname=str(Path('assets') / f_name), data=file_chunks(f.file))

        # Special handling for CWEE projects: add exploits from the "Exploits" note
        all_notes = project.notes.to_ordered_list_flat(project.notes.all())
        added_note_ids = []
        for note in all_notes:
            if (
                (note.title.lower() in ['exploits', 'exploit files', 'exploit scripts'] and note.parent_id is None) or 
                note.parent_id in added_note_ids
            ):
                added_note_ids.append(note.id)
                for f in project.files.all():
                    if note.is_file_referenced(f):
                        f_name = safe_zip_name(f.name)
                        md = md.replace(f'/files/name/{f.name}', f'exploits/{f_name}')
                        z.add(arcname=str(Path('exploits') / f_name), data=file_chunks(f.file))

        z.add(arcname='report.md', data=md.encode())
        
        return StreamingHttpResponseAsync(
            streaming_content=to_chunks(z, allow_small_first_chunk=True),
            content_type='application/zip',
            headers={'Content-Disposition': 'attachment; filename=markdownexport.zip'}
        )

