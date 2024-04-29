import copy
import io
import json
import logging
import tarfile
from pathlib import Path
from typing import Iterable, Optional, Type

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models import Prefetch, prefetch_related_objects
from rest_framework import serializers

from reportcreator_api.archive.import_export.serializers import (
    FindingTemplateExportImportSerializerV2,
    FindingTemplateImportSerializerV1,
    NotesExportImportSerializer,
    PentestProjectExportImportSerializer,
    ProjectTypeExportImportSerializer,
)
from reportcreator_api.pentests.consumers import send_collab_event_project, send_collab_event_user
from reportcreator_api.pentests.models import (
    CollabEvent,
    CollabEventType,
    FindingTemplate,
    PentestFinding,
    PentestProject,
    ProjectMemberInfo,
    ProjectNotebookPage,
    ProjectType,
    ReportSection,
    UserNotebookPage,
)
from reportcreator_api.pentests.serializers.notes import (
    ProjectNotebookPageSerializer,
    ProjectNotebookPageSortListSerializer,
    UserNotebookPageSerializer,
    UserNotebookPageSortListSerializer,
)
from reportcreator_api.users.models import PentestUser
from reportcreator_api.utils.history import history_context

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
                    file_chunks=[archive_data],
                )

                for name, file in serializer.export_files():
                    yield from _tarfile_addfile(
                        buffer=buffer,
                        archive=archive,
                        tarinfo=build_tarinfo(name=name, size=file.size),
                        file_chunks=file.chunks(),
                    )

            design_notice_file = (settings.PDF_RENDER_SCRIPT_PATH / '..' / 'NOTICE_DESIGNS').resolve()
            if context.get('add_design_notice_file') and design_notice_file.is_file():
                design_notice_text = design_notice_file.read_bytes()
                yield from _tarfile_addfile(
                    buffer=buffer,
                    archive=archive,
                    tarinfo=build_tarinfo(name='NOTICE', size=len(design_notice_text)),
                    file_chunks=[design_notice_text],
                )

        yield from _yield_chunks(buffer=buffer, last_chunk=True)
    except Exception as ex:
            logging.exception('Error while exporting archive')
            raise ex


@transaction.atomic()
@history_context(history_change_reason='Imported')
def import_archive(archive_file, serializer_classes: list[Type[serializers.Serializer]], context=None):
    context = (context or {}) | {
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
                data = json.load(archive.extractfile(m))

                serializer = None
                error = None
                for serializer_class in serializer_classes:
                    try:
                        serializer = serializer_class(data=data, context=context)
                        serializer.is_valid(raise_exception=True)
                        error = None
                        break
                    except Exception as ex:
                        serializer = None
                        # Use error of the first failing serializer_class
                        if not error:
                            error = ex
                if error:
                    raise error
                imported_obj = serializer.perform_import()
                for obj in imported_obj if isinstance(imported_obj, list) else [imported_obj]:
                    log.info(f'Imported object {obj=} {obj.id}')
                if isinstance(imported_obj, list):
                    imported_objects.extend(imported_obj)
                else:
                    imported_objects.append(imported_obj)

            return imported_objects
    except Exception as ex:
        # Rollback partially imported data. DB rollback is done in the decorator
        log.exception('Error while importing archive. Rolling back import.')

        for f in context.get('storage_files', []):
            try:
                f.delete(save=False)
            except Exception:
                log.exception(f'Failed to delete imported file "{f.name}" during rollback')

        if isinstance(ex, tarfile.ReadError):
            raise serializers.ValidationError(detail='Could not read .tar.gz file') from ex
        raise ex


def export_templates(data: Iterable[FindingTemplate]):
    return export_archive_iter(data, serializer_class=FindingTemplateExportImportSerializerV2)

def export_project_types(data: Iterable[ProjectType]):
    prefetch_related_objects(data, 'assets')
    return export_archive_iter(data, serializer_class=ProjectTypeExportImportSerializer, context={
        'add_design_notice_file': True,
    })

def export_projects(data: Iterable[PentestProject], export_all=False):
    prefetch_related_objects(
        data,
        Prefetch('findings', PentestFinding.objects.select_related('assignee')),
        Prefetch('sections', ReportSection.objects.select_related('assignee')),
        Prefetch('notes', ProjectNotebookPage.objects.select_related('parent')),
        Prefetch('members', ProjectMemberInfo.objects.select_related('user')),
        'images',
        'project_type__assets',
    )
    return export_archive_iter(data, serializer_class=PentestProjectExportImportSerializer, context={
        'export_all': export_all,
        'add_design_notice_file': True,
    })

def export_notes(project_or_user: PentestProject|PentestUser, notes: Optional[Iterable[ProjectNotebookPage|UserNotebookPage]] = None):
    notes_qs = project_or_user.notes \
        .select_related('parent')
    if notes is not None:
        # Only export sepcified notes and their children
        def get_children_recursive(note, all_notes):
            out = [note]
            for n in all_notes:
                if n.parent_id == note.id:
                    out.extend(get_children_recursive(n, all_notes))
            return out

        all_notes = list(project_or_user.notes.all())
        export_notes = []
        for n in notes:
            if (isinstance(project_or_user, PentestProject) and getattr(n, 'project', None) != project_or_user) or \
                (isinstance(project_or_user, PentestUser) and getattr(n, 'user', None) != project_or_user):
                raise serializers.ValidationError(f'Note {n.id} does not belong to {project_or_user}')
            export_notes.extend(get_children_recursive(n, all_notes))
        notes_qs = notes_qs \
            .filter(id__in=map(lambda n: n.id, export_notes))

    prefetch_related_objects([project_or_user], Prefetch('notes', queryset=notes_qs))
    return export_archive_iter([project_or_user], serializer_class=NotesExportImportSerializer)


def import_templates(archive_file):
    return import_archive(archive_file, serializer_classes=[FindingTemplateExportImportSerializerV2, FindingTemplateImportSerializerV1])

def import_project_types(archive_file):
    return import_archive(archive_file, serializer_classes=[ProjectTypeExportImportSerializer])

def import_projects(archive_file):
    return import_archive(archive_file, serializer_classes=[PentestProjectExportImportSerializer])

def import_notes(archive_file, context):
    if not context.get('project') and not context.get('user'):
        raise ValueError('Either project or user must be provided')
    # Import notes to DB
    notes = import_archive(archive_file, serializer_classes=[NotesExportImportSerializer], context=context)

    # Send collab events
    sender_options = {
        'related_object': context['project'],
        'serializer': ProjectNotebookPageSerializer,
        'serializer_sort': ProjectNotebookPageSortListSerializer,
        'send_collab_event': send_collab_event_project,
    } if context.get('project') else {
        'related_object': context['user'],
        'serializer': UserNotebookPageSerializer,
        'serializer_sort': UserNotebookPageSortListSerializer,
        'send_collab_event': send_collab_event_user,
    }

    # Create events
    events = CollabEvent.objects.bulk_create(
        CollabEvent(
            related_id=sender_options['related_object'].id,
            path=f'notes.{n.note_id}',
            type=CollabEventType.CREATE,
            created=n.created,
            version=n.created.timestamp(),
            data={
                'value': sender_options['serializer'](instance=n).data,
            },
        ) for n in notes
    )
    for e in events:
        sender_options['send_collab_event'](e)

    # Sort event
    notes_sorted = sender_options['related_object'].notes.select_related('parent').all()
    sender_options['serializer_sort'](instance=notes_sorted, context=context).send_collab_event(notes_sorted)

    return notes

