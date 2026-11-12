import enum
import json
from collections.abc import Iterable
from dataclasses import dataclass

from django.core.exceptions import ValidationError

from sysreptor.utils.fielddefinition.types import JsonField


class Permission(enum.StrEnum):
    PROJECT_READ = 'project.read'
    PROJECT_CREATE = 'project.create'
    PROJECT_IMPORT = 'project.import'
    PROJECT_EXPORT = 'project.export'
    PROJECT_EDIT_CONTENT = 'project.edit_content'
    PROJECT_UPDATE_SETTINGS = 'project.update_settings'
    PROJECT_SHARE_NOTES = 'project.share_notes'
    PROJECT_DELETE = 'project.delete'
    PROJECT_ARCHIVE = 'project.archive'
    PROJECT_RESTORE = 'project.restore'

    TEMPLATE_READ = 'template.read'
    TEMPLATE_CREATE = 'template.create'
    TEMPLATE_EDIT = 'template.edit'
    TEMPLATE_DELETE = 'template.delete'
    TEMPLATE_IMPORT = 'template.import'
    TEMPLATE_EXPORT = 'template.export'

    DESIGN_GLOBAL_READ = 'design.global.read'
    DESIGN_GLOBAL_CREATE = 'design.global.create'
    DESIGN_GLOBAL_EDIT = 'design.global.edit'
    DESIGN_GLOBAL_DELETE = 'design.global.delete'
    DESIGN_GLOBAL_IMPORT = 'design.global.import'
    DESIGN_GLOBAL_EXPORT = 'design.global.export'

    USER_LIST_ALL = 'user.list_all'
    USER_CREATE = 'user.create'
    USER_EDIT = 'user.edit'
    USER_DELETE = 'user.delete'

    # Not prefixed with "project." to prevent granting access to all projects via "project.*"
    ARCHIVE_ALWAYS_ADD_ARCHIVING_KEY_TO_PROJECT = 'archive.always_add_archiving_key_to_project'
    ADMIN_ACCESS_ALL_PROJECTS = 'admin.access_all_projects'


def expand_permissions(patterns: Iterable[str]) -> frozenset[Permission]:
    """
    Expand permission patterns (e.g. "template.*") to concrete permissions.
    Unknown permissions are ignored.
    """
    out = set()
    for pattern in patterns or []:
        if pattern.endswith('.*'):
            prefix = pattern[:-1]
            out |= {p for p in Permission if p.value.startswith(prefix)}
        elif pattern in Permission._value2member_map_:
            out.add(Permission(pattern))
    return frozenset(out)


@dataclass(frozen=True)
class Role:
    id: str
    name: str
    permission_patterns: tuple[str, ...]
    description: str | None = None
    is_predefined: bool = False

    @property
    def permissions(self) -> frozenset[Permission]:
        """Expanded concrete permissions used for permission checks."""
        return expand_permissions(self.permission_patterns)


PREDEFINED_USER_ROLES: dict[str, Role] = {r.id: r for r in [
    Role(id='regular_user', name='Regular User', description='Pentesters working on projects they are members of. Read access to templates and designs.', is_predefined=True, permission_patterns=(
        'project.*',
        Permission.TEMPLATE_READ,
        Permission.DESIGN_GLOBAL_READ,
        Permission.DESIGN_GLOBAL_EXPORT,
        Permission.USER_LIST_ALL,
    )),
    Role(id='project_admin', name='Project Admin', description='Access and manage all projects, even without being a member.', is_predefined=True, permission_patterns=(
        'project.*',
        Permission.ADMIN_ACCESS_ALL_PROJECTS,
        Permission.TEMPLATE_READ,
        Permission.DESIGN_GLOBAL_READ,
        Permission.USER_LIST_ALL,
    )),
    Role(id='template_editor', name='Template Editor', description='Create, edit, import, export and delete finding templates.', is_predefined=True, permission_patterns=('template.*',)),
    Role(id='designer', name='Designer', description='Create, edit, import, export and delete global designs.', is_predefined=True, permission_patterns=('design.global.*',)),
    Role(id='user_manager', name='User Manager', description='Create, edit and delete users and assign roles (except superusers).', is_predefined=True, permission_patterns=('user.*',)),
    Role(id='global_archiver', name='Global Archiver', description='Added as key holder to all archived projects. Can archive and restore projects.', is_predefined=True, permission_patterns=(
        Permission.PROJECT_ARCHIVE,
        Permission.PROJECT_RESTORE,
        Permission.ARCHIVE_ALWAYS_ADD_ARCHIVING_KEY_TO_PROJECT,
    )),
]}


USER_ROLE_JSON_FIELD = JsonField(
    required=True,
    schema={
        'type': 'object',
        'required': ['id'],
        'properties': {
            'id': {'type': 'string', 'pattern': r'^[a-zA-Z0-9_-]{1,50}$'},
            'name': {'type': 'string'},
            'description': {'type': 'string'},
            'permissions': {
                'type': 'array',
                'items': {
                    'type': 'string',
                    'enum': [str(p) for p in list(Permission)] + ['project.*', 'template.*', 'design.global.*', 'user.*'],
                },
            },
        },
    },
    label='User role',
    help_text='Example: {"id": "guest", "name": "Guest", "permissions": ["project.read", "project.export", "template.read"]}',
)


def serialize_predefined_user_roles_for_settings() -> list[str]:
    return [json.dumps({
        'id': role.id,
        'name': role.name,
        'description': role.description,
        'permissions': list(role.permission_patterns),
    }, indent=2) for role in PREDEFINED_USER_ROLES.values()]


def get_custom_roles() -> dict[str, Role]:
    from sysreptor.utils.configuration import configuration

    out = {}
    for item in configuration.CUSTOM_USER_ROLES or []:
        r = json.loads(item)
        if not r or not r.get('id') or r['id'] in PREDEFINED_USER_ROLES or r['id'] in out:
            continue
        out[r['id']] = Role(
            id=r['id'],
            name=r.get('name') or r['id'],
            description=r.get('description') or None,
            permission_patterns=tuple(r.get('permissions') or []),
        )
    return out


def get_all_roles() -> dict[str, Role]:
    return PREDEFINED_USER_ROLES | get_custom_roles()


def get_role_permissions(role_ids: Iterable[str], all_roles: dict[str, Role] | None = None) -> frozenset[Permission]:
    all_roles = all_roles if all_roles is not None else get_all_roles()
    out = set()
    for role_id in role_ids or []:
        if role := all_roles.get(role_id):
            out |= role.permissions
    return frozenset(out)


def get_roles_with_permission(permission: str) -> list[str]:
    return [r.id for r in get_all_roles().values() if permission in r.permissions]


def user_has_permission(user, permission: str) -> bool:
    """
    Permission check that also handles anonymous users.
    """
    if not user or getattr(user, 'is_anonymous', True):
        return False
    return user.has_permission(permission)


def validate_custom_roles(custom_roles: list) -> bool:
    role_ids = [json.loads(r).get('id') for r in (custom_roles or [])]
    if duplicates := sorted({str(i) for i in role_ids if role_ids.count(i) > 1}):
        raise ValidationError(f'Duplicate role IDs: {", ".join(duplicates)}')
    for role_id in role_ids:
        if role_id in PREDEFINED_USER_ROLES:
            raise ValidationError(f'Role ID "{role_id}" conflicts with a predefined role')
    return True
