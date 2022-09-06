# User Permissions
The following user permissions are currently available.

## Users without Permissions
Users without dedicated permissions have access to the frontend as regular pentesters. 
They have read and write access to all pentesting reports they are assigned to.

## Template Editor
Users with Template Editor permission are allowed to create, edit and delete finding templates.
Users without this permission have only read access to templates.

## Designer
Users with Designer permission have access to the PDF designer and can create and edit PDF designs.
Users without this permission have only read access to designs.

This privilege potentially allows Template Injections. See [Security Concerns](/designer/security-concerns/) for further information.

## User Manager
User with User Manager permission can create and update other users, 
assign permissions (except Superuser) and
reset passwords (except for Superusers).

Users without this permission can only update their own user information (e.g. name, email, phone number), change their own password, but are not allowed to modify their permissions.

## Superuser
Users with Superuser permission have the highest privileges available. 
They have all permissions without explicitly assigning them.

## Staff
Users with Staff permission are allowed to access the Django backend at https://<sysreptor\>/admin/. 
They see only data they have permissions for.

This permission can be combined with Superuser to have full access to the Django admin interface.
