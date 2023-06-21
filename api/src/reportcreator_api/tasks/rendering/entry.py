import dataclasses
import logging
import uuid
import asyncio
import elasticapm
from asgiref.sync import sync_to_async
from types import NoneType
from typing import Any, Optional, Union
from base64 import b64encode
from django.core.exceptions import ValidationError

from reportcreator_api.tasks.rendering import tasks
from reportcreator_api.pentests import cvss
from reportcreator_api.pentests.customfields.types import FieldDataType, FieldDefinition, EnumChoice
from reportcreator_api.pentests.customfields.utils import HandleUndefinedFieldsOptions, ensure_defined_structure
from reportcreator_api.users.models import PentestUser
from reportcreator_api.utils.error_messages import ErrorMessage, MessageLevel, MessageLocationInfo, MessageLocationType
from reportcreator_api.pentests.models import PentestProject, ProjectType, ProjectMemberInfo
from reportcreator_api.utils.utils import copy_keys, get_key_or_attr


log = logging.getLogger(__name__)



def format_template_field_object(value: dict, definition: dict[str, FieldDefinition], members: Optional[list[dict|ProjectMemberInfo]] = None, require_id=False):
    out = value | ensure_defined_structure(value=value, definition=definition)
    for k, d in (definition or {}).items():
        out[k] = format_template_field(value=out.get(k), definition=d, members=members)

    if require_id and 'id' not in out:
        out['id'] = str(uuid.uuid4())
    return out


def format_template_field_user(value: Union[ProjectMemberInfo, str, uuid.UUID, None], members: Optional[list[dict|ProjectMemberInfo|PentestUser]] = None):
    def format_user(u: Union[ProjectMemberInfo, dict, None]):
        if not u:
            return None
        return copy_keys(
            u.user if isinstance(u, ProjectMemberInfo) else u, 
            ['id', 'name', 'title_before', 'first_name', 'middle_name', 'last_name', 'title_after', 'email', 'phone', 'mobile']) | \
            {'roles': sorted(set(filter(None, get_key_or_attr(u, 'roles', []))), key=lambda r: {'lead': 0, 'pentester': 1, 'reviewer': 2}.get(r, 10))}

    if isinstance(value, (ProjectMemberInfo, PentestUser, dict, NoneType)):
        return format_user(value)
    elif isinstance(value, (str, uuid.UUID)) and (u := next(filter(lambda i: str(get_key_or_attr(i, 'id')) == str(value), members or []), None)):
        return format_user(u)
    elif isinstance(value, (str, uuid.UUID)):
        try:
            return format_user(ProjectMemberInfo(user=PentestUser.objects.get(id=value), roles=[]))
        except (PentestUser.DoesNotExist, ValidationError):
            return None
    else:
        return None


def format_template_field(value: Any, definition: FieldDefinition, members: Optional[list[dict|ProjectMemberInfo]] = None):
    value_type = definition.type
    if value_type == FieldDataType.ENUM:
        return dataclasses.asdict(next(filter(lambda c: c.value == value, definition.choices), EnumChoice(value='', label='')))
    elif value_type == FieldDataType.CVSS:
        score = cvss.calculate_score(value)
        return {
            'vector': value,
            'score': str(round(score, 2)),
            'level': cvss.level_from_score(score).value,
            'level_number': cvss.level_number_from_score(score)
        }
    elif value_type == FieldDataType.USER:
        return format_template_field_user(value, members=members)
    elif value_type == FieldDataType.LIST:
        return [format_template_field(value=e, definition=definition.items, members=members) for e in value]
    elif value_type == FieldDataType.OBJECT:
        return format_template_field_object(value=value, definition=definition.properties, members=members)
    else:
        return value


def format_template_data(data: dict, project_type: ProjectType, imported_members: Optional[list[dict]] = None):
    members = [format_template_field_user(u, members=imported_members) for u in data.get('pentesters', []) + (imported_members or [])]
    data['report'] = format_template_field_object(
        value=ensure_defined_structure(
            value=data.get('report', {}), 
            definition=project_type.report_fields_obj,
            handle_undefined=HandleUndefinedFieldsOptions.FILL_DEFAULT),
        definition=project_type.report_fields_obj, 
        members=members,
        require_id=True)
    data['findings'] = sorted([
        format_template_field_object(
            value=(f if isinstance(f, dict) else {}) | ensure_defined_structure(
                value=f, 
                definition=project_type.finding_fields_obj,
                handle_undefined=HandleUndefinedFieldsOptions.FILL_DEFAULT),
            definition=project_type.finding_fields_obj, 
            members=members,
            require_id=True)
        for f in data.get('findings', [])],
        key=lambda f: (-float(f.get('cvss', {}).get('score', 0)), f.get('created'), f.get('id')))
    data['pentesters'] = sorted( 
        members,
        key=lambda u: (0 if 'lead' in u.get('roles', []) else 1 if 'pentester' in u.get('roles', []) else 2 if 'reviewer' in u.get('roles', []) else 10, u.get('username'))
    )
    return data


async def get_celery_result_async(task):
    while not task.ready():
        await asyncio.sleep(0.2)
    return task.get()
    

@elasticapm.async_capture_span()
async def render_pdf_task(project_type: ProjectType, report_template: str, report_styles: str, data: dict, password: Optional[str] = None, project: Optional[PentestProject] = None) -> dict:
    task = await sync_to_async(tasks.render_pdf_task.delay)(
        template=report_template,
        styles=report_styles,
        data=data,
        language=project.language if project else project_type.language,
        password=password,
        resources=
            {'/assets/name/' + a.name: b64encode(a.file.read()).decode() async for a in project_type.assets.all()} | 
            ({'/images/name/' + i.name: b64encode(i.file.read()).decode() async for i in project.images.all()} if project else {})
    )
    res = await get_celery_result_async(task)
    # Set message location info to ProjectType (if not available)
    for m in res.get('messages', []):
        if not m['location']:
            m['location'] = MessageLocationInfo(type=MessageLocationType.DESIGN, id=project_type.id, name=project_type.name).to_dict()
    return res


async def render_pdf(project: PentestProject, project_type: Optional[ProjectType] = None, report_template: Optional[str] = None, report_styles: Optional[str] = None, password: Optional[str] = None) -> dict:
    if not project_type:
        project_type = project.project_type
    if not report_template:
        report_template = project_type.report_template
    if not report_styles:
        report_styles = project_type.report_styles

    data = {
        'report': {
            'id': str(project.id),
            **project.data,
        },
        'findings': [{
            'id': str(f.finding_id),
            'created': str(f.created),
            **f.data,
        } async for f in project.findings.all()],
        'pentesters': [u async for u in project.members.all()],
    }
    data = await sync_to_async(format_template_data)(data=data, project_type=project_type, imported_members=project.imported_members)
    return await render_pdf_task(
        project=project,
        project_type=project_type,
        report_template=report_template,
        report_styles=report_styles,
        data=data,
        password=password
    )

async def render_pdf_preview(project_type: ProjectType, report_template: str, report_styles: str, report_preview_data: dict) -> dict:
    preview_data = report_preview_data.copy()
    data = await sync_to_async(format_template_data)(data=preview_data, project_type=project_type)
    
    return await render_pdf_task(
        project_type=project_type,
        report_template=report_template,
        report_styles=report_styles,
        data=data
    )

