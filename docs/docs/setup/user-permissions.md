# User Permissions
<span style="color:red;">:octicons-heart-fill-24: Pro only</span>

## Users without dedicated Permissions
Users without dedicated permissions have access to the frontend as regular pentesters. 
They have read and write access to all pentesting reports they are assigned to.

## Template Editor
Template Editors are allowed to create and edit finding templates.
Users without this permission have only read access to templates.

## Designer
Designers can create and edit report designs. Users without this permission can create and edit private designs that cannot be used by other users. They have read access to non-private designs.

## User Manager
User Managers can create and update other users, assign permissions and reset passwords (except superusers).

Users without this permission can only update their own user information (e.g. name, email, phone number), change their own password, but are not allowed to modify their permissions.

## Superuser
Superusers have the highest privileges available.
They have all permissions without explicitly assigning them. They can access all projects, even if they are not members.

**Note:** The permissions of superusers are restricted after login. Superusers must elevate their privileges via the "sudo" button in the toolbar (Pro only). This requires the user to reauthenticate with his password and (if enabled) his second factor.

## Guest
Guest are not allowed to list other users and might be further restricted by the system operator.  
System operators can define if guests should be able to:

* create projects (default: yes)
* import projects (default: no)
* update project settings (default: yes)
* delete projects (default: yes)

:octicons-cloud-24: Cloud · Please contact us and we will reconfigure your installation.

:octicons-server-24: Self-Hosted

Configure your installation by adding the following settings to your `app.env`:
```
GUEST_USERS_CAN_CREATE_PROJECTS=True
GUEST_USERS_CAN_IMPORT_PROJECTS=False
GUEST_USERS_CAN_UPDATE_PROJECT_SETTINGS=True
GUEST_USERS_CAN_DELETE_PROJECTS=True
```
