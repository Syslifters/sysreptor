import enum
from collections.abc import Iterable
from dataclasses import dataclass

from django.core.exceptions import ValidationError


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

    # Not prefixed with "project." to prevent granting access to all projects via "project.*"
    ADMIN_ACCESS_ALL_PROJECTS = 'admin.access_all_projects'

    ARCHIVE_ALWAYS_ADD_ARCHIVING_KEY_TO_PROJECT = 'archive.always_add_archiving_key_to_project'

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
    permissions: frozenset[Permission]
    description: str | None = None
    is_predefined: bool = False


PREDEFINED_ROLES: dict[str, Role] = {r.id: r for r in [
    Role(id='regular_user', name='Regular User', description='Pentesters working on projects they are members of. Read access to templates and designs.', is_predefined=True, permissions=expand_permissions([
        'project.*',
        Permission.TEMPLATE_READ,
        Permission.DESIGN_GLOBAL_READ,
        Permission.DESIGN_GLOBAL_EXPORT,
        Permission.USER_LIST_ALL,
    ])),
    Role(id='project_admin', name='Project Admin', description='Access and manage all projects, even without being a member.', is_predefined=True, permissions=expand_permissions([
        'project.*',
        Permission.ADMIN_ACCESS_ALL_PROJECTS,
        Permission.TEMPLATE_READ,
        Permission.DESIGN_GLOBAL_READ,
        Permission.USER_LIST_ALL,
    ])),
    Role(id='template_editor', name='Template Editor', description='Create, edit, import, export and delete finding templates.', is_predefined=True, permissions=expand_permissions(['template.*'])),
    Role(id='designer', name='Designer', description='Create, edit, import, export and delete global designs.', is_predefined=True, permissions=expand_permissions(['design.global.*'])),
    Role(id='user_manager', name='User Manager', description='Create, edit and delete users and assign roles (except superusers).', is_predefined=True, permissions=expand_permissions(['user.*'])),
    Role(id='global_archiver', name='Global Archiver', description='Added as key holder to all archived projects. Can archive and restore projects.', is_predefined=True, permissions=expand_permissions([
        Permission.PROJECT_ARCHIVE,
        Permission.PROJECT_RESTORE,
        Permission.ARCHIVE_ALWAYS_ADD_ARCHIVING_KEY_TO_PROJECT,
    ])),
]}


def get_custom_roles() -> dict[str, Role]:
    from sysreptor.utils.configuration import configuration

    out = {}
    for r in configuration.CUSTOM_ROLES or []:
        if not isinstance(r, dict) or not r.get('id') or r['id'] in PREDEFINED_ROLES or r['id'] in out:
            continue
        out[r['id']] = Role(
            id=r['id'],
            name=r.get('name') or r['id'],
            description=r.get('description') or None,
            permissions=expand_permissions(r.get('permissions') or []),
        )
    return out


def get_all_roles() -> dict[str, Role]:
    return PREDEFINED_ROLES | get_custom_roles()


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
    role_ids = [r.get('id') for r in custom_roles]
    if duplicates := sorted({str(i) for i in role_ids if role_ids.count(i) > 1}):
        raise ValidationError(f'Duplicate role IDs: {", ".join(duplicates)}')
    for role_id in role_ids:
        if role_id in PREDEFINED_ROLES:
            raise ValidationError(f'Role ID "{role_id}" conflicts with a predefined role')
    return True
