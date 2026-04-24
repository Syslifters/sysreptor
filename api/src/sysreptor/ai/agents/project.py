import dataclasses
import itertools
import textwrap
from uuid import UUID

from asgiref.sync import sync_to_async
from deepagents.middleware._utils import append_to_system_message
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Prefetch
from langchain.agents.middleware import (
    AgentMiddleware,
    AgentState,
)
from langchain.messages import HumanMessage
from langchain.tools import ToolRuntime
from rest_framework.filters import search_smart_split

from sysreptor.ai.agents.base import (
    agent_tool,
    create_sysreptor_agent,
    to_inline_context,
    to_yaml,
)
from sysreptor.pentests.fielddefinition.sort import group_findings
from sysreptor.pentests.models import (
    FindingTemplate,
    PentestFinding,
    PentestProject,
    ProjectNotebookPage,
    ReportSection,
)
from sysreptor.pentests.models.common import get_risk_score_from_data
from sysreptor.pentests.permissions import ProjectSubresourcePermissions
from sysreptor.pentests.rendering.entry import format_template_field_object
from sysreptor.pentests.serializers.notes import ProjectNotebookPageSerializer
from sysreptor.pentests.serializers.project import (
    PentestFindingFromTemplateSerializer,
    PentestFindingSerializer,
    ReportSectionSerializer,
)
from sysreptor.pentests.serializers.template import FindingTemplateSerializer, FindingTemplateShortSerializer
from sysreptor.users.models import PentestUser
from sysreptor.utils.configuration import configuration
from sysreptor.utils.fielddefinition.types import FieldDataType, FieldDefinition, serialize_field_definition
from sysreptor.utils.fielddefinition.utils import get_field_value_and_definition, set_value_at_path
from sysreptor.utils.utils import copy_keys, omit_keys


@dataclasses.dataclass
class ProjectContext:
    project_id: str|UUID
    user_id: str|UUID
    section_id: str|UUID|None = None
    finding_id: str|UUID|None = None


@dataclasses.dataclass
class FakeRequest:
    user: PentestUser|None = None


def get_project(project_id: str, prefetch: bool = False) -> PentestProject:
    qs = PentestProject.objects \
        .filter(id=project_id) \
        .select_related('project_type')
    if prefetch:
        qs = qs.prefetch_related(
            Prefetch('findings', PentestFinding.objects.select_related('assignee')),
            Prefetch('sections', ReportSection.objects.select_related('assignee')),
            Prefetch('notes', ProjectNotebookPage.objects.select_related('parent', 'assignee')))
    return qs.get()


def format_risk_score(data: dict):
    r = get_risk_score_from_data(data)
    return (f'{r["score"]} ' if r.get('score') is not None else '') + str(r.get('level') or 'info')


def format_assignee(assignee: PentestUser|None) -> dict:
    if not assignee:
        return {}
    return {
        'assignee': f'@{assignee.username}' + (f'({assignee.name})' if assignee.name else ''),
    }


def format_section_info(s) -> str:
    return to_inline_context({
        'id': s.section_id,
        'label': s.section_label,
        'status': s.status,
        **format_assignee(s.assignee),
        'data': '...',
    })


def format_project_info(project: PentestProject) -> str:
    findings = [
        format_template_field_object(
            value={'id': str(f.finding_id), 'created': str(f.created), 'order': f.order, **f.data},
            definition=project.project_type.finding_fields_obj,
        ) | {'_meta': {'status': f.status, 'assignee': f.assignee}} for f in project.findings.all()
    ]
    finding_groups = group_findings(
        findings=findings,
        project_type=project.project_type,
        override_finding_order=project.override_finding_order,
    )
    findings_sorted = list(itertools.chain(*[map(lambda f: f | {'_group': g['label']}, g['findings']) for g in finding_groups]))
    is_grouped = len(project.project_type.finding_grouping or []) > 0 and \
        (len(finding_groups) > 1 or (len(finding_groups) == 1 and finding_groups[0]['label']))

    return '<project>' + '\n'.join([
        f'name: {project.name}',
        f'language: {project.get_language_display()}',
        '',
        '## Sections',
        *[format_section_info(s) for s in project.sections.all()],
        '',
        '## Findings',
        *[to_inline_context({
            'id': f['id'],
            'title': f['title'],
            'risk': format_risk_score(f),
            **({'group': f.get('_group', '')} if is_grouped else {}),
            'status': f['_meta']['status'],
            **format_assignee(f['_meta']['assignee']),
            'data': '...',
        }) for f in findings_sorted],
        '',
        '## Notes',
        f'Use {list_notes.name} tool to list all notes.',
    ]) + '</project>'


def format_finding_data(finding) -> str:
    metadata = PentestFindingSerializer(finding).data | {
        'path': f'findings.{finding.finding_id}',
        'risk': format_risk_score(finding.data),
        **format_assignee(finding.assignee),
    }
    finding_data = metadata.pop('data')
    return '<finding>' + '\n'.join([
        '# Finding',
        to_yaml(metadata),
        f'## Data (path: findings.{finding.finding_id}.data)',
        to_yaml(finding_data),
        f'## Field definitions (for findings.{finding.finding_id}.data)',
        format_field_definition(finding.field_definition),
    ]) + '</finding>'


def format_section_data(section) -> str:
    metadata = ReportSectionSerializer(section).data | {
        'path': f'sections.{section.section_id}',
        **format_assignee(section.assignee),
    }
    section_data = metadata.pop('data')
    return '<section>' + '\n'.join([
        '## Section',
        to_yaml(metadata),
        f'### Data (path: sections.{section.section_id}.data)',
        to_yaml(section_data),
        f'### Field definitions (for sections.{section.section_id}.data)',
        format_field_definition(section.field_definition),
    ]) + '</section>'


def format_note_data(note: ProjectNotebookPage) -> str:
    data = ProjectNotebookPageSerializer(note).data | {
        'path': f'notes.{note.note_id}',
        **format_assignee(note.assignee),
    }
    return '<note>' + '\n'.join([
        '# Note',
        to_yaml(data),
    ]) + '</note>'


def format_template_data(template: FindingTemplate, short=False) -> str:
    if short:
        data = copy_keys(FindingTemplateShortSerializer(template, context={'request': None}).data, ['id', 'tags', 'translations'])
    else:
        data = FindingTemplateSerializer(template, context={'request': None}).data
    return '<template>' + '\n'.join([
        '# Template',
        to_yaml({
            'id': template.id,
            'tags': ', '.join(data.get('tags', [])),
        }),
        *itertools.chain.from_iterable([
            f'## Language {tr.get("language")}',
            to_yaml(omit_keys(tr, ['id', 'created', 'updated', 'data'])),
            '### Data',
            to_yaml(tr.get("data", {})),
        ] for tr in data.get('translations', {})),
    ])


def format_field_definition(definition: FieldDefinition):
    data = serialize_field_definition(definition, only_fields=['id', 'type', 'label', 'items', 'properties', 'choices'])
    return to_yaml(data)


def parse_id(value: str, prefix: str) -> str:
    if not prefix.endswith('.'):
        prefix += '.'
    if value.startswith(prefix):
        return value[len(prefix):]
    return value


@agent_tool(parse_docstring=True)
def get_project_info(runtime: ToolRuntime[ProjectContext]) -> str:
    """
    Get an overview of the current pentest project.

    Returns project metadata (name, language), a list of all report sections with
    id, label, status, and assignee, a list of all findings with id, title, risk,
    status, and assignee.
    Use this tool first to understand project structure before calling get_section_data,
    get_finding_data, or get_note_data for specific items.

    When to use:
    - At the start of a task to see what sections and findings exist
    - When the user asks about the project structure or what content is in the report
    - To obtain section_id and finding_id values for subsequent get_section_data / get_finding_data calls
    When not to use:
    - When project overview is already in context inside <navigation> tags.
    """
    project = get_project(runtime.context.project_id)
    return format_project_info(project=project)


@agent_tool(parse_docstring=True)
def get_section_data(runtime: ToolRuntime[ProjectContext], section_id: str) -> tuple[str, dict]:
    """
    Retrieve full data for a specific report section.

    Returns the section metadata and all editable data (e.g. summary, methodology text).

    Args:
        section_id: The section identifier. Use IDs from the project context (e.g.
            "executive_summary", "methodology").
    """
    section_id = parse_id(section_id, 'sections')
    section = get_project(runtime.context.project_id).sections.get(section_id=section_id)
    return format_section_data(section=section), {
        'id': str(section.section_id),
        'title': section.title,
    }


@agent_tool(parse_docstring=True)
def get_finding_data(runtime: ToolRuntime[ProjectContext], finding_id: str) -> tuple[str, dict]:
    """
    Retrieve full data for a specific finding.

    Returns the finding metadata (path, risk, assignee) and all editable data fields
    (e.g. title, cvss, description, recommendation).

    Args:
        finding_id: The finding identifier. Use IDs from the project context (e.g. a
            UUID like "123e4567-e89b-12d3-a456-426614174000").
    """
    finding_id = parse_id(finding_id, 'findings')
    finding = get_project(runtime.context.project_id).findings.get(finding_id=finding_id)
    return format_finding_data(finding=finding), {
        'id': str(finding.finding_id),
        'title': finding.title,
    }


@agent_tool(parse_docstring=True)
def get_note_data(runtime: ToolRuntime[ProjectContext], note_id: str) -> tuple[str, dict]:
    """
    Retrieve full data for a specific project note.

    Returns the note metadata (path, assignee) and content. Notes are organized in a
    tree; use list_notes first to see the note tree and obtain note_id values.

    Args:
        note_id: The note identifier. Use IDs from list_notes output (e.g. a
            UUID like "123e4567-e89b-12d3-a456-426614174000").
    """
    note_id = parse_id(note_id, 'notes')
    note = get_project(runtime.context.project_id).notes.get(note_id=note_id)
    return format_note_data(note=note), {
        'id': str(note.note_id),
        'title': note.title,
    }


@agent_tool(parse_docstring=True)
def list_notes(runtime: ToolRuntime[ProjectContext]) -> str:
    """
    List all notes in the current project as a tree.

    Returns a hierarchical view of notes with id, title, and assignee. Use this to
    discover note_id values before calling get_note_data. Notes are shown with
    indentation indicating parent-child relationships.
    """

    project = get_project(runtime.context.project_id)
    notes_tree = project.notes.to_tree(project.notes.all())

    def format_note_tree(tree, level=0):
        out = []
        for e in tree:
            prefix = '    ' * (level - 1) + '- '
            n = to_inline_context({
                'id': e['note'].note_id,
                # 'parent_id': e['note'].parent.note_id if e['note'].parent else None,
                'title': e['note'].title,
                **format_assignee(e['note'].assignee),
            })
            out.append(prefix + n)
            out.extend(format_note_tree(e['children'], level + 1))
        return out

    return '\n'.join(format_note_tree(notes_tree))


@agent_tool(parse_docstring=True)
def list_templates(runtime: ToolRuntime[ProjectContext], search_terms: str = '') -> str:
    """
    Search for finding templates in the knowledge base.

    Returns templates matching the search (by keywords or tags). Results are ordered
    by relevance, usage, and risk. Use get_template_data with a template_id from
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
def get_template_data(runtime: ToolRuntime[ProjectContext], template_id: str) -> tuple[str, dict]:
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
    list_templates / get_template_data) or create a blank finding and set fields
    in data.

    Workflow with template:
    1. list_templates("xss") or list_templates("sql injection")
    2. get_template_data(template_id) to see template fields
    3. create_finding(template_id=id, data={"title": "Custom Title", ...})

    Workflow without template:
    1. create_finding(data={"title": "New Finding", "description": "...", ...})

    Args:
        data: Optional. Dict of field names to values. Overrides template defaults
            when template_id is set, or finding defaults for a blank finding.
            Use exact field names from get_template_data or the project's finding
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

    return 'Successfully created finding:\n' + format_finding_data(finding=finding), {
        'id': str(finding.finding_id),
        'title': finding.title,
    }


def validate_path(path: str, runtime: ToolRuntime[ProjectContext]) -> dict:
    project = get_project(runtime.context.project_id)
    user = PentestUser.objects.get(id=runtime.context.user_id)
    if not ProjectSubresourcePermissions.has_write_permissions(project=project, user=user):
        raise ValidationError('You do not have write permissions')

    path_parts = tuple(path.split('.'))
    if len(path_parts) < 4:
        raise ValidationError('Invalid path format. Expected format: "<type>.<id>.data.<field_path>". Example: "sections.executive_summary.data.summary"')
    match path_parts[0]:
        case 'findings':
            try:
                obj = project.findings.get(finding_id=path_parts[1])
            except Exception:
                available_findings = [f"{f.finding_id}: {f.title}" for f in project.findings.all()]
                raise ValidationError(
                    f'Finding "{path_parts[1]}" not found. '
                    f'Available findings:\n' + '\n'.join(available_findings),
                ) from None
        case 'sections':
            try:
                obj = project.sections.get(section_id=path_parts[1])
            except Exception:
                available_sections = [f'{s.section_id}: {s.label}' for s in project.sections.all()]
                raise ValidationError(
                    f'Section with ID "{path_parts[1]}" not found. '
                    f'Available sections:\n' + '\n'.join(available_sections),
                ) from None
        case _:
            raise ValidationError(f'Unknown object type: {path_parts[0]}. Only "sections" and "findings" are supported.')
    if path_parts[2] != 'data':
        raise ValidationError('Currently only "data" field updates are supported. Path must contain ".data." as the third component.')

    try:
        data_path, old_value, definition = get_field_value_and_definition(data=obj.data, definition=obj.field_definition, path=path_parts[3:])
    except (KeyError, AttributeError):
        # Provide helpful feedback about available fields
        raise ValidationError(f'Field "{".".join(path_parts[3:])}" not found in {path_parts[0]}. Use get_{path_parts[0][:-1]}_data to see the actual structure. Use exact field names from the returned data.') from None

    return {
        'path': path,
        'data_path': data_path,
        'old_value': old_value,
        'definition': definition,
        'obj': obj,
    }


def update_at_path(info: dict, value):
    updated_data = info['obj'].data
    set_value_at_path(obj=updated_data, path=info['data_path'], value=value)
    # Update in DB
    serializer_class = ReportSectionSerializer if isinstance(info['obj'], ReportSection) else PentestFindingSerializer
    serializer = serializer_class(instance=info['obj'], data={'data': updated_data}, partial=True, context={'project': info['obj'].project})
    serializer.is_valid(raise_exception=True)
    serializer.save()


@agent_tool(parse_docstring=True, metadata={'writable': True})
@transaction.atomic()
def update_field_value(runtime: ToolRuntime[ProjectContext], path: str, value: str|int|float|bool|list|dict) -> str:
    """
    Set a single field in section or finding data (full replacement).

    Replaces the current value of the field at the given path. Use for short
    fields or when replacing an entire field. For long markdown fields where you
    only want to change a substring, use update_markdown_field instead.

    Path format: "<type>.<id>.data.<field_path>"
    - type: "findings" or "sections"
    - id: finding_id or section_id from <navigation> or get_project_info / get_finding_data / get_section_data
    - field_path: dot-separated field names from the actual data (e.g. "title", "description", "summary")

    Args:
        path: Dot-separated path to the field. Examples:
            "findings.123e4567-e89b-12d3-a456-426614174000.data.title",
            "sections.executive_summary.data.summary".
            Use only field names that exist in the project structure (see
            get_finding_data / get_section_data output).
        value: The new value. Replaces the existing value. Type must match the
            field (string, number, boolean, list, or dict).
    """
    res = validate_path(path=path, runtime=runtime)
    update_at_path(info=res, value=value)
    return 'Updated successfully.'


@agent_tool(parse_docstring=True, metadata={'writable': True})
@transaction.atomic()
def update_markdown_field(runtime: ToolRuntime[ProjectContext], path: str, old_text: str, new_text: str) -> str:
    """
    Partially update a markdown field by replacing one substring with another.

    Use this for long markdown content when you only need to change a specific
    sentence or paragraph. The replacement is exact and whitespace-sensitive.
    For replacing the entire field or for short fields, use update_field_value
    instead.

    Path format: same as update_field_value, e.g.
    "findings.<finding_id>.data.description", "sections.<section_id>.data.summary".
    The field must be of type markdown.

    Args:
        path: Dot-separated path to the markdown field (e.g.
            "findings.123e4567-e89b-12d3-a456-426614174000.data.description",
            "sections.executive_summary.data.executive_summary").
        old_text: The exact substring to find and replace. Must appear in the
            current field content; matching is case- and whitespace-sensitive.
        new_text: The replacement text. Inserted in place of old_text.
    """
    res = validate_path(path=path, runtime=runtime)
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


class InjectProjectContextMiddleware(AgentMiddleware[AgentState, ProjectContext]):
    """
    Inject context about the current project and section/finding into the agent.
    Ensure that the agent "sees" the same data as the user in the UI and
    has access to the project structure and the current section/finding data.
    The full data is not saved to history to avoid bloating the chat history.
    """

    @sync_to_async()
    def abefore_agent(self, state, runtime):
        project = get_project(runtime.context.project_id, prefetch=True)

        # Inject short info (ID, title) about the current section/finding
        # Stored in history
        page_id = None
        if section_id := runtime.context.section_id:
            section = next((s for s in project.sections.all() if str(s.section_id) == str(section_id)), None)
            if section:
                page_id = f'sections.{section_id}'
                page_info = format_section_info(section)
        elif finding_id := runtime.context.finding_id:
            finding = next((f for f in project.findings.all() if str(f.finding_id) == str(finding_id)), None)
            if finding:
                page_id = f'findings.{finding_id}'
                page_info = to_inline_context({
                    'id': str(finding.finding_id),
                    'title': finding.title,
                    'risk': format_risk_score(finding.data),
                    'status': finding.status,
                    **format_assignee(finding.assignee),
                    'data': '...',
                })
        if not page_id:
            return

        last_context_msg = next(filter(lambda m: m.additional_kwargs.get('injected_context'), reversed(state['messages'])), None)
        if not last_context_msg or last_context_msg.additional_kwargs.get('injected_context') != page_id:
            # Inject new context hint before last user message
            hint_message = HumanMessage(content=textwrap.dedent(
                f"""\
                <navigation target="{page_id}">
                You are now viewing "{page_id}":
                {page_info}
                </navigation>
                """),
                additional_kwargs={'injected_context': page_id},
            )
            if isinstance(state['messages'][-1], HumanMessage):
                state['messages'].insert(-1, hint_message)

    async def awrap_model_call(self, request, handler):
        # Add instructions how to use the injected context
        CONTEXT_SYSTEM_PROMPT = textwrap.dedent("""\
        ## Context

        <context> and <navigation> are injected with live project data on each turn.

        - <context>: Current project structure (sections, findings, notes list) and, when the user is
          viewing a section or finding, the full data for that item. Always up-to-date.
        - <navigation>: The page the user is currently viewing (e.g. sections.executive_summary,
          findings.<id>).

        When <context> or chat history disagree (e.g. updated title, new finding), treat <context>
        as the source of truth. Use get_finding_data, get_section_data, or get_note_data when you
        need full data for an item not shown in <context>.
        """).strip()
        request = request.override(system_message=append_to_system_message(request.system_message, CONTEXT_SYSTEM_PROMPT))

        # Live context about current project and section/finding
        project = await sync_to_async(get_project)(request.runtime.context.project_id, prefetch=True)
        page_context = []
        if section_id := request.runtime.context.section_id:
            section = next((s for s in project.sections.all() if str(s.section_id) == str(section_id)), None)
            if section:
                page_context = [
                    '## Current Active Section',
                    'Here is the data content of the currently active section:',
                    format_section_data(section=section),
                ]
        elif finding_id := request.runtime.context.finding_id:
            finding = next((f for f in project.findings.all() if str(f.finding_id) == str(finding_id)), None)
            if finding:
                page_context = [
                    '## Current Active Finding',
                    'Here is the data content of the currently active finding:',
                    format_finding_data(finding=finding),
                ]

        context_message = HumanMessage(content='\n'.join([
            '<context>',
            '## Current Project',
            'Here is an overview of the current pentest project structure. It does not contain the '
            'actual content data. Use get_finding_data, get_section_data and get_note_data to '
            'retrieve data content when using findings/sections/notes.',
            format_project_info(project=project),
            '',
            *page_context,
            '</context>',
        ]))

        # Inject into last context message (see abefore_agent) or at start
        last_injected_context_idx = next(
            (i for i in reversed(range(len(request.messages)))
             if request.messages[i].additional_kwargs.get('injected_context')),
            -1,
        )
        if last_injected_context_idx != -1:
            context_message.content = request.messages[last_injected_context_idx].content + '\n\n' + context_message.content
            request = request.override(messages=request.messages[:last_injected_context_idx] + [context_message] + request.messages[last_injected_context_idx + 1:])
        else:
            request = request.override(messages=[context_message] + request.messages)

        return await handler(request)


def init_agent_project_base(additional_system_prompt: str = None, additional_tools: list = None):
    system_prompt = textwrap.dedent(
        """\
        You are SysReptor Copilot, an AI assistant for pentest report writing. You respond with
        text and tool calls. The user sees your responses and tool outputs in real time.

        ## Working with the Project
        When the user asks about or to change report content:
        1. **Use context**: <context> shows current project structure and, when relevant, the
           active section or finding. Use it to see what exists before suggesting or making
           changes.
        2. **Fetch when needed**: Use get_finding_data, get_section_data, or get_note_data when
           you need full content for an item not in <context>.
        3. **Templates**: Use list_templates and get_template_data to search and inspect
           templates before creating findings from them.

        For multi-step or non-trivial tasks, use the write_todos tool to track progress. For
        simple questions or single edits, complete the task directly without todos.

        ## Capabilities
        - Answer questions about the project, findings, sections, and notes
        - Review and give feedback on finding and section content
        - Search and recommend templates; create findings from templates or from scratch
          (when in Agent mode)
        - Edit section and finding fields (when in Agent mode)

        ## Output
        Use Markdown in chat. For code or structured data, use code blocks with four backticks
        and a language identifier.
        """).strip()
    if additional_system_prompt:
        system_prompt += '\n\n' + additional_system_prompt
    if configuration.AI_AGENT_SYSTEM_PROMPT:
        system_prompt += '\n\n' + configuration.AI_AGENT_SYSTEM_PROMPT
    return create_sysreptor_agent(
        system_prompt=system_prompt,
        tools=[
            get_project_info,
            get_note_data,
            get_section_data,
            get_finding_data,
            list_notes,
            list_templates,
            get_template_data,
        ] + (additional_tools or []),
        middleware=[
            InjectProjectContextMiddleware(),
        ],
        context_schema=ProjectContext,
    )


def init_agent_project_ask():
    return init_agent_project_base(
        additional_system_prompt=textwrap.dedent("""\
        ## Ask Mode
        You are in Ask mode: read-only. You can view project structure, findings, sections, and
        notes but cannot create or edit anything. Provide information, answer questions, and
        offer insights. Do not suggest calling write or update tools — you do not have them in
        this mode.
        """).strip(),
    )


def init_agent_project_agent():
    return init_agent_project_base(
        additional_system_prompt=textwrap.dedent("""\
        ## Agent Mode
        You are in Agent mode: full write access.
        You can create findings (from templates or blank), update section and finding fields
        (update_field_value for full replacement, update_markdown_field for partial markdown
        edits). Read data before editing; use the path format shown in the tool descriptions.
        """).strip(),
        additional_tools=[
            update_field_value,
            update_markdown_field,
            create_finding,
        ],
    )

