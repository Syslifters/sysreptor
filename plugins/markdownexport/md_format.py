import itertools
import json

from sysreptor.pentests.rendering.entry import format_project_template_data
from sysreptor.plugins import FieldDataType, FieldDefinition


def format_heading(value: str, level: int|None = None):
    value = value or ''
    heading_level = level or 1
    if heading_level <= 6:
        return f"{'#' * heading_level} {value}\n\n"
    else:
        return f"**{value}**\n\n"


def format_field_object(value, definition, context=None):
    context = (context or {}).copy()
    heading_level = context.pop('heading_level', 0) + 1
    skip_heading = context.pop('skip_heading', [])
    skip_fields = context.pop('skip_fields', [])

    fields_formatted = []
    for f in definition.fields:
        if f.id in skip_fields:
            continue

        heading_formatted = ''
        if f.id in skip_heading:
            heading_formatted = ''
            heading_level -= 1
        elif isinstance(definition, FieldDefinition):
            heading_formatted = format_heading(f.label or f.id, level=heading_level)
        else:
            heading_formatted = format_heading(f.label or f.id, level=7)
        
        content_formatted = format_field_value(value=value.get(f.id), definition=f, context=context | {'heading_level': heading_level})

        fields_formatted.append(heading_formatted + content_formatted)
    return '\n\n'.join(fields_formatted) + '\n\n\n'


def format_field_value(value, definition, context=None):
    if value is None:
        return ''
    
    if (
        definition.type == FieldDataType.LIST and \
        definition.items.type == FieldDataType.OBJECT and \
        set(definition.items.keys()) == {'title', 'content'}
    ):
        # Special handling for list of sections
        fields_formatted = []
        for v in value:
            title = format_heading(format_field_value(value=v.get('title'), definition=definition.items['title'], context=context), level=context.get('heading_level', 0) + 1)
            content = format_field_value(value=v.get('content'), definition=definition.items['content'], context=context)
            fields_formatted.append(title + content)
        return '\n\n'.join(fields_formatted) + '\n\n'
    elif definition.type == FieldDataType.OBJECT:
        return format_field_object(value=value, definition=definition, context=context)
    elif definition.type == FieldDataType.LIST:
        if definition.items.type in [FieldDataType.MARKDOWN, FieldDataType.OBJECT, FieldDataType.LIST, FieldDataType.JSON]:
            return '\n\n'.join(format_field_value(value=v, definition=definition.items, context=context) for v in value)
        else:
            return '\n'.join('* ' + format_field_value(value=v, definition=definition.items, context=context) for v in value)
    elif definition.type == FieldDataType.JSON:
        try:
            value = json.dumps(json.loads(value), indent=2)
        except json.JSONDecodeError:
            pass
        return f'```json\n{value}\n```'
    elif definition.type == FieldDataType.CVSS:
        return f"{value['vector']} ({value['score']} - {value['level'].title()})"
    elif definition.type == FieldDataType.CWE:
        return value['value']
    elif definition.type == FieldDataType.ENUM:
        return value['label']
    elif definition.type == FieldDataType.USER:
        return value['name']
    else:
        return str(value)


def format_section(data, section, context=None):
    context = context or {}
    heading_level = context.get('heading_level', 0) + 1
    first_field = next(iter(section.field_definition.fields), None)
    skip_heading = first_field and (first_field.id == section.section_id or first_field.label == section.title)

    section_heading = format_heading(section.title or section.section_id, level=heading_level)
    section_content = format_field_object(value=data, definition=section.field_definition, context=context | {
        'heading_level': heading_level,
        'skip_heading': [first_field.id] if skip_heading else [],
    })
    return section_heading + section_content


def format_finding(data, definition, context=None):
    context = context or {}
    heading_level = context.get('heading_level', 0) + 1

    finding_heading = format_heading(data.get('title'), level=heading_level)
    finding_content = format_field_object(value=data, definition=definition, context=context | {
        'heading_level': heading_level,
        'skip_fields': ['title'],
    })
    return finding_heading + finding_content


def format_project(project):
    data = format_project_template_data(project)
    md = format_heading(data['report'].get('title'), level=1)

    appendix_sections = []
    sections = project.sections.all()
    for sd in project.project_type.report_sections:
        section = next((s for s in sections if s.section_id == sd.get('id')), None)
        if not section:
            continue
        elif any(n in section.section_id for n in ['appendix', 'appendices']):
            appendix_sections.append(section)
            continue
        md += format_section(data=data['report'], section=section, context={'heading_level': 1, 'skip_fields': ['title']})
    
    md += format_heading('Findings', level=2)
    for finding in list(itertools.chain(*map(lambda g: g['findings'], data.get('finding_groups', [])))):
        md += format_finding(data=finding, definition=project.project_type.finding_fields_obj, context={'heading_level': 2})

    for section in appendix_sections:
        md += format_section(data=data['report'], section=section, context={'heading_level': 1})
    return md

