# Audit Log
<BadgePro />

Professional installations record sensitive actions in an audit log.

## Access

Open the log as an active superuser:

1. Log in.
2. Elevate your privileges with **Enable Superuser Permissions** in the main menu. This requires reauthentication with your password and, if enabled, your second factor.
3. Open `/admin/audit/auditlogentry/`.

## Recorded actions

### Authentication

* **Successful login** (`login_success`)
* **Logout** (`logout`)
* **Superuser permissions enabled** (`admin_enabled`) and **disabled** (`admin_disabled`)

### Users

* **User created** (`user_created`)
* **User updated** (`user_updated`)
* **User deleted** (`user_deleted`)
* **Permissions updated** (`user_permissions_updated`)
* **Password changed** (`password_changed`)

### Credentials

* **MFA method created** (`mfa_created`) and **removed** (`mfa_deleted`)
* **Auth identity created** (`auth_identity_created`) and **removed** (`auth_identity_deleted`)
* **API token created** (`api_token_created`)

### Projects and notes

* **Project member added** (`project_member_added`) and **removed** (`project_member_removed`)
* **Note share created** (`note_share_created`)

### Instance

* **Backup started** (`backup_started`) and **backup restored** (`restore`)
* **Settings changed** (`settings_changed`)
* **License changed** (`license_changed`)
* **Migration** (`migration`)
