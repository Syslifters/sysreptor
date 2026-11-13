# User Permissions
<BadgePro />

Permissions are granted to users via roles.
Each user can have multiple roles and has the combined permissions of all assigned roles.
SysReptor ships with [predefined roles](#predefined-roles). You can define additional [custom roles](#custom-roles) with fine-grained permissions.

Roles are assigned by users with the `user.edit` permission (e.g. admins or [User Managers](#user-manager)) in the user management.
New users get the roles configured in [`DEFAULT_USER_ROLES`](/setup/configuration#roles) (default: `regular_user`).

**Project membership is separate from roles.** Being listed as a project member does not grant permissions by itself. Global user roles define what a user can do; membership decides which projects those `project.*` permissions apply to. Users without any roles cannot access any projects, even if they are members.

Custom roles, superuser elevation, archiving, and note sharing depend on your license and instance configuration. Permissions for unavailable or disabled features have no effect.


## Predefined Roles

### Regular User
Regular users work as pentesters on projects they are members of (role ID: `regular_user`).
They have full project capabilities (`project.*`) on those projects, including create, edit, export, delete, archive, and restore.
They cannot access projects they are not members of.
They can read finding templates and designs, and see all users.

### Project Admin
Project Admins can access and manage all projects, even if they are not members (role ID: `project_admin`).
They have the same project, template, design, and user-listing capabilities as regular users, plus `admin.access_all_projects`.

### Designer
Designers can create, edit, import, export, and delete **global** report designs (role ID: `designer`).
Users who only have `design.global.read` (typically via `regular_user`) can read global designs but not manage them.
If [private designs](/setup/configuration#private-designs) are enabled, users can create private designs that other users cannot see. Private designs do not require the Designer role.

### Template Editor
Template Editors can create, edit, import, export, and delete finding templates (role ID: `template_editor`).
Users who only have `template.read` (typically via `regular_user`) can read templates but not manage them.

### User Manager
User Managers can create, edit, and delete users, assign roles, and reset passwords (except superusers) (role ID: `user_manager`).

Users without `user.edit` can only update their own user information (e.g. name, email, phone number) and change their own password. They cannot modify their own roles and permissions.

### Global Archiver
Global Archivers are always added as key holders to [archived projects](/insights/archiving), even if they are not project members (role ID: `global_archiver`). They can restore all archived projects where they were added as key holders.
The Global Archiver role alone does not grant access to all projects.


## Custom Roles
Custom roles allow you to grant fine-grained permissions to users, e.g. to restrict capabilities of users or external contractors.
Configure them via [`CUSTOM_USER_ROLES`](/setup/configuration#roles): a JSON list of role objects.
Custom role IDs must not conflict with predefined role IDs.

```json title="Example: Restricted guest role"
CUSTOM_USER_ROLES='[
  {
    "id": "guest",
    "name": "Guest",
    "description": "External users with restricted permissions",
    "permissions": ["project.read", "project.edit_content", "template.read"]
  }
]'
```

Wildcards (e.g. `project.*`) grant all permissions with the given prefix.

### Available Permissions

| Permission | Description |
| --- | --- |
| `project.read` | Read projects the user is a member of. Required for all other project permissions |
| `project.create` | Create and copy projects |
| `project.import` | Import projects |
| `project.export` | Export projects |
| `project.edit_content` | Edit content of projects (sections, findings, notes, images, files) |
| `project.update_settings` | Update project settings (e.g. name, design, members, finished/readonly state) |
| `project.share_notes` | Create and manage note sharing links |
| `project.delete` | Delete projects |
| `project.archive` | Archive projects |
| `project.restore` | Restore archived projects |
| `template.read` | Read finding templates |
| `template.create` | Create and copy finding templates |
| `template.edit` | Edit finding templates |
| `template.delete` | Delete finding templates |
| `template.import` | Import finding templates |
| `template.export` | Export finding templates |
| `design.global.read` | Read global designs |
| `design.global.create` | Create and copy global designs |
| `design.global.edit` | Edit global designs |
| `design.global.delete` | Delete global designs |
| `design.global.import` | Import global designs |
| `design.global.export` | Export global designs |
| `user.list_all` | See all users on the SysReptor instance. Otherwise only users working in the same projects are listed |
| `user.create` | Create users |
| `user.edit` | Edit other users, assign roles, reset passwords and manage MFA methods, identities and API tokens (except superusers) |
| `user.delete` | Delete users |
| `archive.always_add_archiving_key_to_project` | Always added as key holder to archived projects (if a public key is configured), even if not a member |
| `admin.access_all_projects` | Access all projects, even if not a member (additionally requires `project.read`) |


## Superuser
Superusers can obtain the highest privileges available.
By default they only have the permissions from their assigned roles.
After elevating privileges, they have all permissions and can access all projects, even if they are not members.

**Note:** Superusers must elevate their privileges via the "Enable Superuser Permissions" button in the main menu (Pro only). This requires the user to reauthenticate with their password and (if enabled) their second factor.


## System Users
System users are marked with the **Is system user** flag (not a role ID).
They have no normal permissions and are intended only for creating backups via API.
System users cannot be used in projects, templates, and designs.
This flag can only be set via the Django interface:

1. Log in with superuser permissions
2. Elevate your privileges using the "Enable Superuser Permissions" button
3. Access https://sysreptor.example.com/admin/users/pentestuser/
4. Choose the user
5. Tick "Is system user"
6. Save

Use system users only for backups.


## Migration from Guest Users
Previous versions of SysReptor had an "Is Guest" flag with permissions configured via `GUEST_USERS_CAN_*` settings.
Guest users are migrated to a custom role `guest` that is created from your previous `GUEST_USERS_CAN_*` settings (if guest users exist).
Other users get the `regular_user` role plus one role for each previously assigned permission (Project Admin, Designer, Template Editor, User Manager, Global Archiver).
