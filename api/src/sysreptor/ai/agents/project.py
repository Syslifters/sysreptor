import dataclasses
import itertools
import textwrap
from typing import Any
from uuid import UUID

from asgiref.sync import sync_to_async
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Prefetch
from langchain.agents import create_agent
from langchain.agents.middleware import AgentState, ClearToolUsesEdit, ContextEditingMiddleware, before_agent
from langchain.messages import HumanMessage
from langchain.tools import ToolRuntime
from langgraph.runtime import Runtime
from rest_framework.filters import search_smart_split

from sysreptor.ai.agents.base import (
    ClearOldInjectedContextEdit,
    agent_tool,
    fix_broken_tool_calls,
    init_chat_model,
    to_inline_context,
    to_yaml,
)
from sysreptor.ai.agents.checkpointer import DjangoModelCheckpointer
from sysreptor.pentests.fielddefinition.sort import group_findings
from sysreptor.pentests.models import PentestProject, ProjectNotebookPage, ReportSection
from sysreptor.pentests.models.common import get_risk_score_from_data
from sysreptor.pentests.models.template import FindingTemplate
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
from sysreptor.utils.utils import copy_keys


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
        qs = qs.prefetch_related('findings', 'sections', Prefetch('notes', ProjectNotebookPage.objects.select_related('parent')))
    return qs.get()


def format_risk_score(data: dict):
    r = get_risk_score_from_data(data)
    return (f'{r["score"]} ' if r.get('score') is not None else '') + (r.get('level') or 'info')


def format_assignee(assignee: PentestUser|None) -> dict:
    if not assignee:
        return {}
    return {
        'assignee': f'@{assignee.username}' + (f'({assignee.name})' if assignee.name else ''),
    }


def format_project_info(project: PentestProject) -> str:
    findings = [
        format_template_field_object(
            value={'id': str(f.id), 'created': str(f.created), 'order': f.order, **f.data},
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

    project_info = {
        'name': project.name,
        'language': project.get_language_display(),
        'sections': [to_inline_context({
            'id': s.section_id,
            'title': s.title,
            'status': s.status,
            **format_assignee(s.assignee),
            'data': '...',
        }) for s in project.sections.all()],
        'findings': [to_inline_context({
            'id': f['id'],
            'title': f['title'],
            'risk': format_risk_score(f),
            **({'group': f.get('_group', '')} if is_grouped else {}),
            'status': f['_meta']['status'],
            **format_assignee(f['_meta']['assignee']),
            'data': '...',
        }) for f in findings_sorted],
        'notes': [to_inline_context({
            'id': n.note_id,
            'parent_id': n.parent.note_id if n.parent else None,
            'title': n.title,
            **format_assignee(n.assignee),
        }) for n in project.notes.all()],
    }
    return f'<project>{to_yaml(project_info)}</project>'


def format_finding_data(finding) -> str:
    r = get_risk_score_from_data(finding.data)
    data = PentestFindingSerializer(finding).data | {
        'risk_score': r.get('score'),
        'risk_level': r.get('level'),
    }
    return f'<finding path="findings.{finding.finding_id}">{to_yaml(data)}</finding>'


def format_section_data(section) -> str:
    data = ReportSectionSerializer(section).data
    return f'<section path="sections.{section.section_id}">{to_yaml(data)}</section>'


def format_note_data(note: ProjectNotebookPage) -> str:
    data = ProjectNotebookPageSerializer(note).data
    return f'<note path="notes.{note.note_id}">{to_yaml(data)}</note>'


def format_template_data(template: FindingTemplate, short=False) -> str:
    if short:
        data = copy_keys(FindingTemplateShortSerializer(template, context={'request': None}).data, ['id', 'tags', 'translations'])
    else:
        data = FindingTemplateSerializer(template, context={'request': None}).data
    return f'<template id="{template.id}">{to_yaml(data)}</template>'


def format_field_definition(definition: FieldDefinition):
    data = serialize_field_definition(definition, only_fields=['id', 'type', 'label', 'items', 'properties', 'choices', 'cvss_version'])
    return to_yaml(data)


def parse_id(value: str, prefix: str) -> str:
    if not prefix.endswith('.'):
        prefix += '.'
    if value.startswith(prefix):
        return value[len(prefix):]
    return value


@agent_tool(parse_docstring=True)
def get_section_data(runtime: ToolRuntime[ProjectContext], section_id: str) -> str:
    """
    Get data for a specific section by its section_id.

    Args:
        section_id: The ID of the section to retrieve. Must be a valid section_id from the project (e.g. "executive_summary", "methodology"). Use the section IDs shown in the project context.
    """
    section_id = parse_id(section_id, 'sections')
    section = get_project(runtime.context.project_id).sections.get(section_id=section_id)
    return format_section_data(section=section), {
        'id': str(section.section_id),
        'title': section.title,
    }


@agent_tool(parse_docstring=True)
def get_finding_data(runtime: ToolRuntime[ProjectContext], finding_id: str) -> str:
    """
    Get data for a specific finding by its finding_id.

    Args:
        finding_id: The ID of the finding to retrieve. Must be a valid finding_id from the project (e.g. a UUID like "123e4567-e89b-12d3-a456-426614174000"). Use the finding IDs shown in the project context.
    """
    finding_id = parse_id(finding_id, 'findings')
    finding = get_project(runtime.context.project_id).findings.get(finding_id=finding_id)
    return format_finding_data(finding=finding), {
        'id': str(finding.finding_id),
        'title': finding.title,
    }


@agent_tool(parse_docstring=True)
def get_note_data(runtime: ToolRuntime[ProjectContext], note_id: str) -> str:
    """
    Get data for a specific note by its note_id.

    Args:
        note_id: The ID of the note to retrieve.
    """
    note_id = parse_id(note_id, 'notes')
    note = get_project(runtime.context.project_id).notes.get(note_id=note_id)
    return format_note_data(note=note), {
        'id': str(note.note_id),
        'title': note.title,
    }


@agent_tool(parse_docstring=True)
def list_templates(runtime: ToolRuntime[ProjectContext], search_terms: str|None = None) -> list[dict]:
    """
    Search for finding templates matching a query.

    Args:
        search_terms: Search terms containing keywords or tags separated by spaces. All terms must be present in the template. (e.g. "xss", "sql injection")
    """
    project = get_project(runtime.context.project_id)
    qs = FindingTemplate.objects.all()
    if search_terms:
        qs = qs.search(search_smart_split(search_terms.strip()))
    qs = qs.annotate_risk_level_number() \
        .order_by_language(project.language) \
        .prefetch_related('translations') \
        .order_by('-has_language', *(['-search_rank'] if search_terms else []), '-usage_count', '-risk_level_number', '-risk_score_number', '-created')

    results = []
    for t in qs[:100]:
        results.append(f'<template>{format_template_data(t, short=True)}</template>')
    if results:
        return '\n'.join(results)
    else:
        return 'No matching templates found.'


@agent_tool(parse_docstring=True)
def get_template_data(runtime: ToolRuntime[ProjectContext], template_id: str) -> str:
    """
    Get data for a specific finding template by its ID.

    Args:
        template_id: The ID of the finding template to retrieve. Use list_templates tool to search for templates.
    """
    template = FindingTemplate.objects \
        .prefetch_related('translations') \
        .get(id=template_id)
    return format_template_data(template=template), {
        'id': str(template.id),
        'title': template.main_translation.title,
    }


@agent_tool(parse_docstring=True, metadata={'writable': True})
def create_finding(runtime: ToolRuntime[ProjectContext], data: dict|None = None, template_id: str|None = None, template_language: str|None = None) -> str:
    """
    Create a new finding. Optionally based on a finding template.

    Args:
        data: (Optional) Data for the new finding as a dictionary of fields. Fields not specified will be set to the template value or default value.
        template_id: (Optional) The ID of the finding template to use as a base for the new finding.
        template_language: (Optional) The language of the finding template to use. If not specified, the template's main translation will be used.
    """

    project = get_project(runtime.context.project_id)
    user = PentestUser.objects.get(id=runtime.context.user_id)
    if not ProjectSubresourcePermissions.has_write_permissions(project=project, user=user):
        raise ValidationError('You do not have write permissions')

    serializer_context = {'project': project, 'request': FakeRequest(user=user)}
    if template_id:
        serializer = PentestFindingFromTemplateSerializer(data={
            'template': template_id,
            'template_language': template_language,
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
        raise ValidationError(f'Field "{".".join(path_parts[3:])}" not found in {path_parts[0]}. Use get_{path_parts[0][:-1]}_data tool first to see available fields.') from None

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
def update_field_value(runtime: ToolRuntime[ProjectContext], path: str, value: Any) -> None:
    """
    Set a field in section or finding data.

    Args:
        path: The dot-separated path to the field to update. Format: "<type>.<id>.data.<field_name>". e.g. "findings.123e4567-e89b-12d3-a456-426614174000.data.title", "sections.executive_summary.data.summary". Use only field names that exist in the project structure shown in the context.
        value: The new value to set. Replaces the existing value. Type must match the field type (string, number, boolean, etc.).
    """
    res = validate_path(path=path, runtime=runtime)
    update_at_path(info=res, value=value)
    return 'Updated successfully.'


@agent_tool(parse_docstring=True, metadata={'writable': True})
@transaction.atomic()
def update_markdown_field(runtime: ToolRuntime[ProjectContext], path: str, old_text: str, new_text: str) -> str:
    """
    Partially update a markdown field by replacing old_text with new_text.
    Use this tool for updating parts of large markdown texts. For short fields or non-markdown fields, use `update_field_value` instead.

    Args:
        path: The dot-separated path to the markdown field e.g. "findings.<finding_id>.data.description", "sections.<section_id>.data.executive_summary"
        old_text: The text content to replace. If this doesn't match exactly, the update will fail..
        new_text: The new text content to insert in place of old_text.
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


@before_agent
@sync_to_async
def inject_project_context(state: AgentState, runtime: Runtime):
    """
    Inject current project context into the message history.
    Project overview is added as the first message. It is updated whenever the project structure changes (e.g. new finding/note added).

    Working context (current section/finding data) is added before the last user message.
    Whenever the working context changes, a new message is injected. The old one is preserved in history.
    """

    project = get_project(runtime.context.project_id, prefetch=True)

    # section_definitions = [
    #     f'<fielddefinition path="sections.{s.section_id}.data">{format_field_definition(definition=s.field_definition)}</fielddefinition>'
    #     for s in project.sections.all()]
    # f"""\
    # Available findings field definitions:
    # <fielddefinition path="findings.finding_id.data">{format_field_definition(project.project_type.finding_fields_obj)}</fielddefinition>

    # Available sections field definitions:
    # {'\n'.join(section_definitions)}

    project_context_message = HumanMessage(content=textwrap.dedent(
        """\
        ## Current Project Context
        {data}

        This is a overview of the project structure and field definitions.
        Data of sections, findings and notes can be retrieved via tools.
        """).format(data=format_project_info(project=project)),
        additional_kwargs={'injected_context': 'project_overview'},
    )

    if (
        len(state['messages']) > 0 and
        state['messages'][0].additional_kwargs.get('injected_context') == 'project_overview'
    ):
        # Replace existing project context message
        if state['messages'][0].content != project_context_message.content:
            state['messages'][0] = project_context_message
    else:
        state['messages'].insert(0, project_context_message)

    working_context_message = None
    if section_id := runtime.context.section_id:
        section = project.sections.filter(section_id=section_id).first()
        if section:
            working_context_message = textwrap.dedent(
                """\
                ## Current Working Context
                You are working on this section:
                {data}
                """).format(data=format_section_data(section=section))
    elif finding_id := runtime.context.finding_id:
        finding = project.findings.filter(finding_id=finding_id).first()
        if finding:
            working_context_message = textwrap.dedent(
                """\
                ## Current Working Context
                You are working on this finding:
                {data}
                """).format(data=format_finding_data(finding=finding))

    if working_context_message:
        current_context_msg = any(filter(
            lambda m: m.additional_kwargs.get('injected_context') == 'working_context' and m.content == working_context_message,
            state['messages']))
        if not current_context_msg and isinstance(state['messages'][-1], HumanMessage):
            state['messages'].insert(-1, HumanMessage(
                content=working_context_message,
                additional_kwargs={
                    'injected_context': 'working_context',
                    'cache_control': {'type': 'ephemeral'},
                },
            ))


def init_agent_project_ask(additional_system_prompt: str = None, additional_tools: list = None):
    system_prompt = textwrap.dedent("""\
        You are SysReptor Copilot, a specialized AI agent designed to assist users in writing pentest reports.
        You have access to the current project's data including report sections, findings and notes.
        """).replace('\n', ' ').strip()
    if additional_system_prompt:
        system_prompt += '\n\n' + additional_system_prompt
    if configuration.AI_AGENT_SYSTEM_PROMPT:
        system_prompt += '\n\n' + configuration.AI_AGENT_SYSTEM_PROMPT

    agent = create_agent(
        model=init_chat_model(),
        checkpointer=DjangoModelCheckpointer(),
        tools=[
            get_note_data,
            get_section_data,
            get_finding_data,
            list_templates,
            get_template_data,
        ] + (additional_tools or []),
        middleware=[
            ContextEditingMiddleware(edits=[
                ClearToolUsesEdit(),
                ClearOldInjectedContextEdit(),
            ]),
            inject_project_context,
            fix_broken_tool_calls,
        ],
        system_prompt=system_prompt,
        context_schema=ProjectContext,
    )
    return agent


def init_agent_project_agent():
    return init_agent_project_ask(
        additional_system_prompt=textwrap.dedent("""\
        IMPORTANT TOOL USAGE GUIDELINES:
        1. Always use the exact IDs shown in the project context when calling tools
        2. For update_field_value, use only field paths that exist in the project structure
        3. Before updating fields, retrieve the current data first to understand the structure
        4. Field paths must follow the format: "<type>.<id>.data.<field_name>" (e.g., "sections.executive_summary.data.summary")
        5. Do not invent or guess field names - only use fields you have seen in the context or retrieved data
        """).replace('\n', ' ').strip(),
        additional_tools=[
            update_field_value,
            update_markdown_field,
            create_finding,
        ],
    )

