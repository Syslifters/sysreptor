from pathlib import Path

import zipstream
from django.db.models import Prefetch, prefetch_related_objects
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


class MarkdownExportView(ProjectSubresourceMixin, GenericAPIView):
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES
    serializer_class = Serializer

    def post(self, request, *args, **kwargs):
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
                md = md.replace(f'/images/name/{f.name}', 'assets/' + f.name)
                z.add(arcname=str(Path('assets') / f.name), data=file_chunks(f.file))

        if 'cwee' in project.project_type.name.lower():
            # Special handling for CWEE projects: add exploits from the "Exploits" note
            for note in project.notes.all():
                if not ('exploits' in note.title.lower() and not note.parent_id):
                    continue
                for f in project.files.all():
                    if note.is_file_referenced(f):
                        md = md.replace(f'/files/name/{f.name}', f'exploits/{f.name}')
                        z.add(arcname=str(Path('exploits') / f.name), data=file_chunks(f.file))

        z.add(arcname='report.md', data=md.encode())
        
        return StreamingHttpResponseAsync(
            streaming_content=to_chunks(z, allow_small_first_chunk=True),
            content_type='application/zip',
        ) 


# TODO: markdownexport plugin
# * [x] urls
# * [x] view
# * [x] markdown export logic
#   * [x] zipstream with markdown and images
#   * [x] rewrite image paths
#   * [x] format fields
#   * [x] format title, sections, findings
#   * [x] appendix section after findings
#   * [x] table of contents: below title => generate via python (only finding/section headings)
#   * [x] CWEE special handling (if "CWEE" in project_type.name): copy files from note "Exploits" (and sub-notes?) to zip in "exploits" folder
# * [ ] frontend
#   * [ ] download button
#   * [ ] warnings: for project via checks API endpoint
#   * [ ] warning: CWEE add exploits to zip ???
#   * [ ] warning: features not supported: template variables, template language, generated content, review content
# * [x] tests
#   * [x] test formatting all field types
#   * [x] test nested fields (list, object)
#   * [x] test headline formatting
#   * [x] test section/finding order
#   * [x] test API requests: returns zip with report.md and images
#   * [x] test permissions: user not in project
# * [ ] docs
#   * [ ] plugins table
#   * [ ] plugin readme
# * [ ] changelog
