# User Permissions
<span style="color:red;">:octicons-heart-fill-24: Pro only</span>

## Users without dedicated Permissions
Users without dedicated permissions have access to the frontend as regular pentesters. 
They have only read-write access to pentesting reports they are assigned to.  
They cannot read other pentesting reports.

## Superuser
Superusers have the highest privileges available.
They have all permissions without explicitly assigning them. They can access all projects, even if they are not members.

**Note:** The permissions of superusers are restricted after login. Superusers must elevate their privileges via the "sudo" button in the toolbar (Pro only). This requires the user to reauthenticate with his password and (if enabled) his second factor.

## User Manager
User Managers can create and update other users, assign permissions and reset passwords (except superusers).

Users without this permission can only update their own user information (e.g. name, email, phone number), change their own password, but are not allowed to modify their permissions.

## Designer
Designers can create and edit report designs. Users without this permission can create and edit private designs that cannot be used by other users. They have read access to non-private designs.

## Template Editor
Template Editors are allowed to create and edit finding templates.
Users without this permission have only read access to templates.

## Guest
Guest users have read-write access to projects they are assigned to.

Guest are not allowed to list other users and might be further restricted by the system operator:

* create projects (default: yes)
* import projects (default: no)
* update project settings (default: yes)
* delete projects (default: yes)

:octicons-cloud-24: Cloud · Please [contact us](../../contact-us.md){ target=_blank } and we will reconfigure your installation.

:octicons-server-24: Self-Hosted

Configure your installation by adding the following settings to your `app.env`:
```
GUEST_USERS_CAN_CREATE_PROJECTS=True
GUEST_USERS_CAN_IMPORT_PROJECTS=False
GUEST_USERS_CAN_UPDATE_PROJECT_SETTINGS=True
GUEST_USERS_CAN_DELETE_PROJECTS=True
```

## System
System is a special privilege that allows users to create backups via API. This privilege can only be set via the Django interface:

1. Log in with superuser permissions
2. Elevate your privileges using the "sudo" button
3. Access https://sysreptor.example.com/admin/users/pentestuser/
4. Choose the user
5. Tick "Is system user"
6. Save

The `system` permission should only be used for backups.