from deepagents.backends.protocol import FILE_NOT_FOUND
from django.core.exceptions import ValidationError
from django.db import transaction
from langchain.tools import ToolRuntime
from rest_framework.filters import search_smart_split

from sysreptor.ai.agents.filesystem import ProjectFilesystemBackend
from sysreptor.ai.agents.project import (
    NOTE_FIELD_DEFINITION,
    FakeRequest,
    ProjectContext,
    format_note_info,
    format_template_data,
    get_note_data,
    get_project,
)
from sysreptor.ai.agents.tools import agent_tool
from sysreptor.pentests.models import FindingTemplate, NoteType, ProjectNotebookPage, ReportSection
from sysreptor.pentests.permissions import ProjectSubresourcePermissions
from sysreptor.pentests.serializers.notes import ProjectNotebookPageCreateSerializer, ProjectNotebookPageSerializer
from sysreptor.pentests.serializers.project import (
    PentestFindingFromTemplateSerializer,
    PentestFindingSerializer,
    ReportSectionSerializer,
)
from sysreptor.users.models import PentestUser
from sysreptor.utils.fielddefinition.types import FieldDataType
from sysreptor.utils.fielddefinition.utils import get_field_value_and_definition, set_value_at_path


@agent_tool(parse_docstring=True)
def list_notes(runtime: ToolRuntime[ProjectContext]) -> str:
    """
    List all notes in the current project as a tree.

    Returns a hierarchical view of notes with id, title, file path, and assignee.
    Indentation indicates parent-child relationships. Use read_file on the file
    path to get full note content.

    """
    project = get_project(runtime.context.project_id)
    notes_tree = project.notes.to_tree(project.notes.all())

    def format_note_tree(tree, level=0):
        out = []
        for e in tree:
            prefix = '  ' * level + '- '
            out.append(prefix + format_note_info(e['note']))
            out.extend(format_note_tree(e['children'], level + 1))
        return out

    return '\n'.join(format_note_tree(notes_tree))


@agent_tool(parse_docstring=True)
def list_templates(runtime: ToolRuntime[ProjectContext], search_terms: str = '') -> str:
    """
    Search for finding templates in the knowledge base.

    Returns templates matching the search (by keywords or tags). Results are ordered
    by relevance, usage, and risk. Use read_template with a template_id from
    this list to get full template structure before creating a finding.

    Args:
        search_terms: Optional. Space-separated keywords or tags; all terms must be
            present in the template (e.g. "xss", "sql injection"). If omitted, returns
            all templates ordered by usage and risk.
    """
    project = get_project(runtime.context.project_id)
    qs = FindingTemplate.objects.all()
    search_terms = (search_terms or '').strip()
    if search_terms:
        qs = qs.search(search_smart_split(search_terms))
    qs = qs.annotate_risk_level_number() \
        .order_by_language(project.language) \
        .prefetch_related('translations') \
        .order_by('-has_language', *(['-search_rank'] if search_terms else []), '-usage_count', '-risk_level_number', '-risk_score_number', '-created')

    results = []
    for t in qs[:100]:
        results.append(format_template_data(t, short=True))
    if results:
        return '\n'.join(results)
    else:
        return 'No matching templates found.'


@agent_tool(parse_docstring=True)
def read_template(runtime: ToolRuntime[ProjectContext], template_id: str) -> tuple[str, dict]:
    """
    Retrieve full structure and content of a finding template.

    Returns the template id, tags, and per-language data (title, cvss, description,
    recommendation, etc.). Use this after list_templates to inspect a template
    before creating a finding with create_finding(template_id=...).

    Args:
        template_id: The template ID from list_templates (e.g. numeric or UUID
            identifier shown in search results).
    """
    template = FindingTemplate.objects \
        .prefetch_related('translations') \
        .get(id=template_id)
    return format_template_data(template=template), {
        'id': str(template.id),
        'title': template.main_translation.title,
    }


@agent_tool(parse_docstring=True, metadata={'writable': True})
def create_finding(runtime: ToolRuntime[ProjectContext], data: dict = None, template_id: str = '', template_language: str = '') -> tuple[str, dict]:
    """
    Create a new finding in the project, optionally from a template.

    Use this tool to add a new finding. You can base it on a template (from
    list_templates / read_template) or create a blank finding and set fields
    in data.

    Workflow with template:
    1. list_templates("xss") or list_templates("sql injection")
    2. read_template(template_id) to see template fields
    3. create_finding(template_id=id, data={"title": "Custom Title", ...})

    Workflow without template:
    1. create_finding(data={"title": "New Finding", "description": "...", ...})

    Args:
        data: Optional. Dict of field names to values. Overrides template defaults
            when template_id is set, or finding defaults for a blank finding.
            Use exact field names from read_template or the project's finding
            field definition.
        template_id: Optional. Template ID from list_templates to base the finding on.
        template_language: Optional. Language code for the template (defaults to
            the template's main language).
    """

    project = get_project(runtime.context.project_id)
    user = PentestUser.objects.get(id=runtime.context.user_id)
    if not ProjectSubresourcePermissions.has_write_permissions(project=project, user=user):
        raise ValidationError('You do not have write permissions')

    serializer_context = {'project': project, 'request': FakeRequest(user=user)}
    if template_id:
        serializer = PentestFindingFromTemplateSerializer(data={
            'template': template_id or None,
            'template_language': template_language or None,
            'data': data or {},
        }, context=serializer_context)
        serializer.is_valid(raise_exception=True)
        finding = serializer.save()
    else:
        serializer = PentestFindingSerializer(data={'data': data or {}}, context=serializer_context)
        serializer.is_valid(raise_exception=True)
        finding = serializer.save()

    finding_data = ProjectFilesystemBackend(runtime=runtime).read(file_path=f'/reporting/findings/{finding.finding_id}.yaml').file_data.get('content', '')
    file_path = f'{ProjectFilesystemBackend.PROJECT_ROOT}/reporting/findings/{finding.finding_id}.yaml'
    return f'Successfully created finding at {file_path}:\n' + finding_data, {
        'id': str(finding.finding_id),
        'title': finding.title,
    }


@agent_tool(parse_docstring=True, metadata={'writable': True})
def create_note(
    runtime: ToolRuntime[ProjectContext],
    data: dict = None,
    parent: str = '',
    order: int | None = None,
) -> tuple[str, dict]:
    """
    Create a new note in the project.

    Use list_notes to see the note tree and valid parent note IDs. Set parent and
    order to control placement in the hierarchy; put note content fields in data.

    Args:
        data: Optional. Note content fields, e.g. {"title": "...", "text": "..."}.
            May include title, text, checked, and icon_emoji.
        parent: Optional parent note ID from list_notes. Omit or leave empty for
            a top-level note.
        order: Optional 1-based position among siblings with the same parent.
            Existing notes at or after this position are shifted down. When omitted,
            the note is appended at the end of its sibling group.
    """
    project = get_project(runtime.context.project_id)
    user = PentestUser.objects.get(id=runtime.context.user_id)
    if not ProjectSubresourcePermissions.has_write_permissions(project=project, user=user):
        raise ValidationError('You do not have write permissions')

    serializer_data = dict(data or {})
    if parent:
        serializer_data['parent'] = parent
    if order is not None:
        serializer_data['order'] = order

    serializer = ProjectNotebookPageCreateSerializer(
        data=serializer_data,
        context={'project': project},
    )
    serializer.is_valid(raise_exception=True)
    note = serializer.save()

    note_data = ProjectFilesystemBackend(runtime=runtime).read(
        file_path=f'/notes/{note.note_id}.yaml',
    ).file_data.get('content', '')
    file_path = f'{ProjectFilesystemBackend.PROJECT_ROOT}/notes/{note.note_id}.yaml'
    return f'Successfully created note at {file_path}:\n' + note_data, {
        'id': str(note.note_id),
        'title': note.title,
    }


def validate_path(file_path: str, field: str, runtime: ToolRuntime[ProjectContext]) -> dict:
    project = get_project(runtime.context.project_id)
    user = PentestUser.objects.get(id=runtime.context.user_id)
    if not ProjectSubresourcePermissions.has_write_permissions(project=project, user=user):
        raise ValidationError('You do not have write permissions')

    filepath_parts = tuple(file_path.strip('/').split('/'))
    if len(filepath_parts) < 3 or filepath_parts[0] != 'project':
        raise ValidationError('File not found.')
    obj_id = filepath_parts[-1][:-5] if filepath_parts[-1].endswith('.yaml') else filepath_parts[-1]
    if len(filepath_parts) == 4 and filepath_parts[1] == 'reporting':
        resource_type = filepath_parts[2]
    elif len(filepath_parts) == 3:
        resource_type = filepath_parts[1]
    else:
        raise ValidationError('File not found.')
    match resource_type:
        case 'findings':
            try:
                obj = project.findings.get(finding_id=obj_id)
            except Exception:
                raise ValidationError(FILE_NOT_FOUND) from None
        case 'sections':
            try:
                obj = project.sections.get(section_id=obj_id)
            except Exception:
                raise ValidationError(FILE_NOT_FOUND) from None
        case 'notes':
            try:
                obj = project.notes.get(note_id=obj_id)
            except Exception:
                raise ValidationError(FILE_NOT_FOUND) from None
        case _:
            raise ValidationError(
                'File not found. Only files in "/project/reporting/sections/", '
                '"/project/reporting/findings/" and "/project/notes/" directories are supported.',
            )

    field_parts = tuple(field.split('.'))
    try:
        if isinstance(obj, ProjectNotebookPage):
            if obj.type == NoteType.EXCALIDRAW and field_parts and field_parts[0] == 'text':
                raise ValidationError('Cannot write to "text" for excalidraw notes. Use the excalidraw note endpoints/tools instead.')
            data_path, old_value, definition = get_field_value_and_definition(
                data=get_note_data(obj),
                definition=NOTE_FIELD_DEFINITION,
                path=field_parts,
            )
        else:
            if field_parts[0] != 'data':
                raise ValidationError('Currently only "data" field updates are supported. Field path must contain "data." as the first component.')
            data_path, old_value, definition = get_field_value_and_definition(
                data=obj.data, definition=obj.field_definition, path=field_parts[1:],
            )
    except (KeyError, AttributeError):
        # Provide helpful feedback about available fields
        raise ValidationError(f'Field "{field}" not found in {file_path}. Use read_file to see the actual structure. Use exact field names from the returned data.') from None

    return {
        'file_path': file_path,
        'field': field,
        'data_path': data_path,
        'old_value': old_value,
        'definition': definition,
        'obj': obj,
    }


def update_at_path(info: dict, value):
    obj = info['obj']
    if isinstance(obj, ProjectNotebookPage):
        serializer = ProjectNotebookPageSerializer(
            instance=obj,
            data={info['data_path'][0]: value},
            partial=True,
            context={'project': obj.project},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
    else:
        updated_data = obj.data
        set_value_at_path(obj=updated_data, path=info['data_path'], value=value)
        # Update in DB
        serializer_class = ReportSectionSerializer if isinstance(obj, ReportSection) else PentestFindingSerializer
        serializer = serializer_class(instance=obj, data={'data': updated_data}, partial=True, context={'project': obj.project})
        serializer.is_valid(raise_exception=True)
        serializer.save()


@agent_tool(parse_docstring=True, metadata={'writable': True})
@transaction.atomic()
def update_field_value(runtime: ToolRuntime[ProjectContext], file_path: str, field: str, value: str|int|float|bool|list|dict) -> str:
    """
    Set a single field in section, finding, or note data (full replacement).

    Replaces the current value of the field at the given path. Use for short
    fields or when replacing an entire field. For long markdown fields where you
    only want to change a substring, use update_markdown_field instead.

    Args:
        file_path: The file path to the section, finding, or note file. Examples:
            /project/reporting/findings/123e4567-e89b-12d3-a456-426614174000.yaml,
            /project/reporting/sections/executive_summary.yaml,
            /project/notes/123e4567-e89b-12d3-a456-426614174000.yaml
        field: Dot-separated path to the field inside the file.
            e.g. "data.title", "data.summary", "data.affected_components.[0]".
            Use only field names that exist in the project structure (see read_file
            output for the corresponding /project/... path).
        value: The new value. Replaces the existing value. Type must match the
            field (string, number, boolean, list, or dict).
    """
    res = validate_path(file_path=file_path, field=field, runtime=runtime)
    update_at_path(info=res, value=value)
    return 'Updated successfully.'


@agent_tool(parse_docstring=True, metadata={'writable': True})
@transaction.atomic()
def update_markdown_field(runtime: ToolRuntime[ProjectContext], file_path: str, field: str, old_text: str, new_text: str) -> str:
    """
    Partially update a markdown field by replacing one substring with another.

    Use this for long markdown content when you only need to change a specific
    sentence or paragraph. The replacement is exact and whitespace-sensitive.
    For replacing the entire field or for short fields, use update_field_value
    instead. The field must be of type markdown.

    Args:
        file_path: The file path to the section, finding, or note file. Examples:
            /project/reporting/findings/123e4567-e89b-12d3-a456-426614174000.yaml,
            /project/reporting/sections/executive_summary.yaml,
            /project/notes/123e4567-e89b-12d3-a456-426614174000.yaml
        field: Dot-separated path to the field inside the file.
            e.g. "data.summary", "data.recommendation".
            Use only field names that exist in the project structure (see read_file
            output for the corresponding /project/... path).
        old_text: The exact substring to find and replace. Must appear in the
            current field content; matching is case- and whitespace-sensitive.
        new_text: The replacement text. Inserted in place of old_text.
    """
    res = validate_path(file_path=file_path, field=field, runtime=runtime)
    if res['definition'].type != FieldDataType.MARKDOWN:
        raise ValidationError('Field is not of type markdown.')

    current_value = res['old_value'] or ''
    if not old_text:
        raise ValidationError(f'old_text cannot be empty. Specify the text you want to replace or use `{update_field_value.name}` instead.')
    elif not current_value:
        raise ValidationError(f'The field is empty. Use `{update_field_value.name}` instead.')

    # Find the old_text in current_value
    old_text_index = current_value.find(old_text)
    if old_text_index == -1:
        # Show a preview of current content
        preview_len = min(200, len(current_value))
        preview = current_value[:preview_len]
        if len(current_value) > preview_len:
            preview += '...'
        raise ValidationError('Could not find the specified old_text in the field. The content may have been modified by another user.')

    # Perform the replacement
    updated_value = current_value[:old_text_index] + new_text + current_value[old_text_index + len(old_text):]
    update_at_path(info=res, value=updated_value)
    return 'Updated successfully'
