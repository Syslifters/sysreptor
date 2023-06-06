import copy
import io
import json
import logging
import tarfile
from pathlib import Path
from typing import Iterable, Type
from django.conf import settings
from django.http import FileResponse
from rest_framework import serializers
from django.db import transaction
from django.db.models import prefetch_related_objects, Prefetch
from django.core.serializers.json import DjangoJSONEncoder

from reportcreator_api.archive.import_export.serializers import FindingTemplateExportImportSerializer, PentestProjectExportImportSerializer, ProjectTypeExportImportSerializer
from reportcreator_api.pentests.models import FindingTemplate, NotebookPage, PentestFinding, PentestProject, ProjectMemberInfo, ProjectType, ReportSection


log = logging.getLogger(__name__)


BLOCKSIZE = settings.FILE_UPLOAD_MAX_MEMORY_SIZE


def build_tarinfo(name, size):
    info = tarfile.TarInfo(name=name)
    info.size = size
    return info


def _yield_chunks(buffer: io.BytesIO, last_chunk=False):
    """
    Split buffer in chunks of BLOCKSIZE and yield them.
    Removes the returned chunks form the buffer.
    If last_chunks=True, return the last chunk even if it is less than BLOCKSIZE
    """
    val = buffer.getvalue()
    buffer.truncate(0)
    buffer.seek(0)
    
    num_chunks, len_remaining = divmod(len(val), BLOCKSIZE)
    for i in range(num_chunks):
        yield val[i * BLOCKSIZE:(i + 1) * BLOCKSIZE]

    if len_remaining > 0:
        remaining = val[-len_remaining:]
        if last_chunk:
            yield remaining
        else:
            buffer.write(remaining)


def _tarfile_addfile(buffer, archive: tarfile.TarFile, tarinfo, file_chunks) -> Iterable[bytes]:
    """
    Re-implementation of TarFile.addfile() that yields chunks to integrate into Django StreamingHttpResponse
    """
    archive._check("awx")

    tarinfo = copy.copy(tarinfo)

    buf = tarinfo.tobuf(archive.format, archive.encoding, archive.errors)
    archive.fileobj.write(buf)
    archive.offset += len(buf)

    # re-implemented copyfileobj with yield after each block
    for chunk in file_chunks:
        archive.fileobj.write(chunk)
        yield from _yield_chunks(buffer)
    
    blocks, remainder = divmod(tarinfo.size, tarfile.BLOCKSIZE)
    if remainder > 0:
        archive.fileobj.write(tarfile.NUL * (tarfile.BLOCKSIZE - remainder))
        blocks += 1
    archive.offset += blocks * tarfile.BLOCKSIZE
    yield from _yield_chunks(buffer)

    archive.members.append(tarinfo)


def export_archive_iter(data, serializer_class: Type[serializers.Serializer], context=None) -> Iterable[bytes]:
    try:
        buffer = io.BytesIO()

        with tarfile.open(fileobj=buffer, mode='w|gz') as archive:
            context = (context or {}) | {
                'archive': archive,
            }
            for obj in data:
                serializer = serializer_class(instance=obj, context=context)
                data = serializer.export()
                archive_data = json.dumps(data, cls=DjangoJSONEncoder).encode()
                yield from _tarfile_addfile(
                    buffer=buffer, 
                    archive=archive,
                    tarinfo=build_tarinfo(name=f'{obj.id}.json', size=len(archive_data)), 
                    file_chunks=[archive_data]
                )
                
                for name, file in serializer.export_files():
                    yield from _tarfile_addfile(
                        buffer=buffer,
                        archive=archive,
                        tarinfo=build_tarinfo(name=name, size=file.size), 
                        file_chunks=file.chunks()
                    )

        yield from _yield_chunks(buffer=buffer, last_chunk=True)
    except Exception as ex:
            logging.exception('Error while exporting archive')
            raise ex


@transaction.atomic()
def import_archive(archive_file, serializer_class: Type[serializers.Serializer]):
    context = {
        'archive': None,
        'storage_files': [],
    }

    try:
        # We cannot use the streaming mode for import, because random access is required for importing files referenced in JSON
        # However, the tarfile library does not load everything into memory at once, only the archive member metadata (e.g. filename)
        # File contents are loaded only when reading them, but file reading can be streamed
        with tarfile.open(fileobj=archive_file, mode='r') as archive:
            context['archive'] = archive

            # Get JSON files to import
            to_import = []
            for m in archive.getmembers():
                mp = Path(m.name)
                if m.isfile() and mp.match('*.json') and not mp.parent.parts:
                    to_import.append(m.name)

            # Perform import
            # The actual work is performed in serializers
            imported_objects = []
            for m in to_import:
                serializer = serializer_class(data=json.load(archive.extractfile(m)), context=context)
                serializer.is_valid(raise_exception=True)
                obj = serializer.perform_import()
                log.info(f'Imported object {obj=} {obj.id=}')
                imported_objects.append(obj)
            
            return imported_objects
    except Exception as ex:
        # Rollback partially imported data. DB rollback is done in the decorator
        log.exception('Error while importing archive. Rolling back import.')

        for f in context.get('storage_files', []):
            try:
                f.delete(save=False)
            except Exception:
                log.exception(f'Failed to delete imported file "{f.name}" during rollback')
        raise ex


def export_templates(data: Iterable[FindingTemplate]):
    return export_archive_iter(data, serializer_class=FindingTemplateExportImportSerializer)

def export_project_types(data: Iterable[ProjectType]):
    prefetch_related_objects(data, 'assets')
    return export_archive_iter(data, serializer_class=ProjectTypeExportImportSerializer)

def export_projects(data: Iterable[PentestProject], export_all=False):
    prefetch_related_objects(
        data, 
        Prefetch('findings', PentestFinding.objects.select_related('assignee')), 
        Prefetch('sections', ReportSection.objects.select_related('assignee')), 
        Prefetch('notes', NotebookPage.objects.select_related('parent')),
        Prefetch('members', ProjectMemberInfo.objects.select_related('user')),
        'images', 
        'project_type__assets',
    )
    return export_archive_iter(data, serializer_class=PentestProjectExportImportSerializer, context={
        'export_all': export_all,
    })


def import_templates(archive_file):
    return import_archive(archive_file, serializer_class=FindingTemplateExportImportSerializer)

def import_project_types(archive_file):
    return import_archive(archive_file, serializer_class=ProjectTypeExportImportSerializer)

def import_projects(archive_file):
    return import_archive(archive_file, serializer_class=PentestProjectExportImportSerializer)

