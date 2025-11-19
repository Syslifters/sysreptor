# Configuration
`app.env` (located in `deploy` directory) controls the behaviour of your SysReptor installation.
[Server settings](#server-settings) are defined in `app.env` and passed as environment variables to the SysReptor docker container.
[Application settings](#application-settings) can be configured in `app.env` or via the settings page in the web interface.

After making changes, go to `sysreptor/deploy` and restart the containers:

```shell
docker compose up -d
```


## Server Settings
:octicons-server-24: Self-Hosted


### Django Secret Key
Django server secret key (see https://docs.djangoproject.com/en/stable/ref/settings/#std-setting-SECRET_KEY).
Make sure this key remains secret.

``` title="Generate random secret key:"
printf "SECRET_KEY=$(openssl rand -base64 64 | tr -d '\n=')\n"
```

``` title="Example (regenerate this value!):"
SECRET_KEY="TODO-change-me-Z6cuMithzO0fMn3ZqJ7nTg0YJznoHiJXoJCNngQM4Kqzzd3fiYKdVx9ZidvTzqsm"
```

If you renew the Django secret key, all existing sessions terminate and links for setting new passwords (e.g., from password reset emails) are invalidated.

### Data Encryption at Rest
Encrypt data at rest by configuring an encryption key. This will encrypt sensitive data in your database and files uploaded in your notes (~~except images~~, images are also encrypted).

Database and file storage administrators cannot access encrypted data. The key is held in the web application. Data encryption at rest does not help against malicious actors with access to the web server.

You have to define one `DEFAULT_ENCRYPTION_KEY_ID` which will be used for data encryption. However, you can rotate your keys by defining multiple keys in `ENCRYPTION_KEYS`.  
All specified keys are used for decrypting stored data.

Note that the `DEFAULT_ENCRYPTION_KEY_ID` must be part of `ENCRYPTION_KEYS`.

```  title="Generate random encryption keys:"
KEY_ID=$(uuidgen) && printf "ENCRYPTION_KEYS=[{\"id\": \"${KEY_ID}\", \"key\": \"$(openssl rand -base64 32)\", \"cipher\": \"AES-GCM\", \"revoked\": false}]\nDEFAULT_ENCRYPTION_KEY_ID=\"${KEY_ID}\"\n"
```

``` title="Example (regenerate these values!):"
ENCRYPTION_KEYS='[{"id": "TODO-change-me-unique-key-id-5cdda4c0-a16c-4ae2-8a16-aa2ff258530d", "key": "256 bit (32 byte) base64 encoded AES key", "cipher": "AES-GCM", "revoked": false}]'
DEFAULT_ENCRYPTION_KEY_ID="TODO-change-me-unique-key-id-5cdda4c0-a16c-4ae2-8a16-aa2ff258530d"
```


### Debug mode
Debug mode enables Django's debug toolbar and stack traces. Do not use debug mode in production environments.

``` title="Example:"
DEBUG=off
```


### Allowed Hosts
Comma-separated allowed hostnames/domain names for this installation.

``` title="Example:"
ALLOWED_HOSTS="sysreptor.example.com,sysreptor.example.local"
```


### FIDO2/WebAuthn
If you want to use FIDO2/WebAuthn for MFA, you have to define the hostname ([WebAuthn Relying Party ID](https://www.w3.org/TR/webauthn-2/#relying-party-identifier)) of your installation.

``` title="Example:"
MFA_FIDO2_RP_ID="sysreptor.example.com"
```


### License Key
<span style="color:red;">:octicons-heart-fill-24: Pro only</span>

License key for SysReptor Professional.

``` title="Example:"
LICENSE="your-license-key"
```


### S3 Storage
Uploaded files and images can be stored in an S3 bucket. Files are stored on the filesystem in a docker volume by default. If data at rest encryption is configured, all uploaded files (incl. images) are encrypted.

`DEFAULT_S3_*` settings to apply to all file storages. It is possible to configure different settings per storage.


``` title="Global storage configuration: store everything in S3 bucket"
DEFAULT_STORAGE="s3"  # Default: "filesystem"
DEFAULT_S3_ACCESS_KEY="access-key"
DEFAULT_S3_SECRET_KEY="secret-key"
DEFAULT_S3_SESSION_TOKEN="session-token"  # optional
DEFAULT_S3_BUCKET_NAME="bucket-name"
DEFAULT_S3_ENDPOINT_URL="endpoint-url"
```

``` title="Uploaded file storage configuration"
UPLOADED_FILE_STORAGE="s3"  # Default: "filesystem"
UPLOADED_FILE_S3_ACCESS_KEY="access-key"
UPLOADED_FILE_S3_SECRET_KEY="secret-key"
UPLOADED_FILE_S3_SESSION_TOKEN="session-token"  # optional
UPLOADED_FILE_S3_BUCKET_NAME="bucket-name"
UPLOADED_FILE_S3_ENDPOINT_URL="endpoint-url"
UPLOADED_FILE_LOCATION="uploadedfiles"
```

``` title="Uploaded image storage configuration"
UPLOADED_IMAGE_STORAGE="s3"  # Default: "filesystem"
UPLOADED_IMAGE_S3_ACCESS_KEY="access-key"
UPLOADED_IMAGE_S3_SECRET_KEY="secret-key"
UPLOADED_IMAGE_S3_SESSION_TOKEN="session-token"  # optional
UPLOADED_IMAGE_S3_BUCKET_NAME="bucket-name"
UPLOADED_IMAGE_S3_ENDPOINT_URL="endpoint-url"
UPLOADED_IMAGE_LOCATION="uploadedimages"
```

``` title="Uploaded asset storage configuration"
UPLOADED_ASSET_STORAGE="s3"  # Default: "filesystem"
UPLOADED_ASSET_S3_ACCESS_KEY="access-key"
UPLOADED_ASSET_S3_SECRET_KEY="secret-key"
UPLOADED_ASSET_S3_SESSION_TOKEN="session-token"  # optional
UPLOADED_ASSET_S3_BUCKET_NAME="bucket-name"
UPLOADED_ASSET_S3_ENDPOINT_URL="endpoint-url"
UPLOADED_ASSET_LOCATION="uploadedasset"
```

Archived project files can also be uploaded to an S3 bucket. Archives are stored on the filesystem in a docker volume by default.

``` title="Archived file storage configuratio"
ARCHIVED_FILE_STORAGE="s3"  # Default: "filesystem"
ARCHIVED_FILE_S3_ACCESS_KEY="access-key"
ARCHIVED_FILE_S3_SECRET_KEY="secret-key"
ARCHIVED_FILE_S3_SESSION_TOKEN="session-token"  # optional
ARCHIVED_FILE_S3_BUCKET_NAME="bucket-name"
ARCHIVED_FILE_S3_ENDPOINT_URL="endpoint-url"
ARCHIVED_FILE_LOCATION="archivedfiles"
```

### Emails
SysReptor sends emails for password resets. Configure the SMTP server to use for sending emails.
See https://docs.djangoproject.com/en/stable/ref/settings/#email-host

``` title="Email settings"
EMAIL_HOST=mail.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=on
EMAIL_HOST_USER=username
EMAIL_HOST_PASSWORD=password
DEFAULT_FROM_EMAIL=sysreptor@example.com
```

To test your email settings, you can run the following command:

```bash title="Send test email"
docker compose run --rm --no-TTY app python3 manage.py sendtestemail <your-email@example.com>
```


### Backup Key
<span style="color:red;">:octicons-heart-fill-24: Pro only</span>

The backup key is used for creating backups via the [web interface](backups.md#create-backups-via-web-interface) or the [REST API](backups.md#create-backups-via-api). The key should be random and must have 20 or more characters.  
Make sure this key remains secret.

``` title="Generate random backup key:"
printf "BACKUP_KEY=$(openssl rand -base64 25 | tr -d '\n=')\n"
```

``` title="Example (do not use this value!):"
BACKUP_KEY="WfyqYzRVZAOFbCtltYEFN36XBzRz6Ys6ZA"
```

Backup requests via the web interface or the REST API are long running requests that need to download a large backup file. These requests might be aborted when `gunicorn` server worker processes are restarted and the backup request exceeds the restart timeout. This timeout can be increased by setting the following value.

``` title="Example:"
SERVER_WORKER_RESTART_TIMEOUT=3600  # 1 hour
```


### Reverse Proxy
Interpret `X-Forwarded-*` headers when SysReptor is behind a reverse proxy. 
See also https://docs.djangoproject.com/en/stable/ref/settings/#use-x-forwarded-host

```
USE_X_FORWARDED_HOST=on
USE_X_FORWARDED_PORT=on
```

When SysReptor is accessible via HTTPS (recommended), use following setting to redirect all HTTP requests to HTTPS.
This flag also enables setting the `Secure` flag for cookies.
```
SECURE_SSL_REDIRECT=on
```

### Proxy Server
Set the proxy variables `HTTP_PROXY`, `HTTPS_PROXY` and `NO_PROXY` to allow outbound connections using a proxy server.

```bash title="Example:"
HTTP_PROXY="http://192.168.0.111:8080"
HTTPS_PROXY="http://192.168.0.111:8080"
```

!!! info "The proxy server must be reachable from container"

    Make sure that the proxy server is reachable from inside your docker container.
    Loopback addresses (e. g. `127.0.0.1`) or `localhost` will not work.


### Custom CA Certificates
If your SysReptor is behind a proxy with a custom certificate, you can use this setting to specify your custom CA certificates.

```
CA_CERTIFICATES="-----BEGIN CERTIFICATE-----\nMIIDqDCCApCgAwIBAgIFAMjv7sswDQYJKoZIhv..."
```

### WebSockets
Disable WebSockets and always use HTTP fallback for collaborative editing. 
This is not recommended because some features are only available with WebSockets and HTTP fallback has higher latency.
This setting sould only be activated if WebSockets are blocked by a firewall or not supported by a reverse proxy.

``` title="Example:"
DISABLE_WEBSOCKETS=true
```

### Plugins
Extend the functionality of SysReptor by enabling plugins. Plugins are disabled by default and need to be explicitly enabled.
`ENABLED_PLUGINS` is a comma separated list of plugin names or plugin IDs.

``` title="Example:"
ENABLED_PLUGINS="cyberchef,graphqlvoyager,checkthehash"
```

Some plugins require additional configuration. These plugin settings are configured as separate entries in `app.env` or via the settings page in the web interface.
Please refer to the plugin documentation for more information on available plugin setting.






## Application Settings

:octicons-server-24: Self-Hosted :octicons-cloud-24: Cloud

Application settings can be configured in `app.env` or via the settings page in the web interface (stored in the database).
When a setting is configured both in `app.env` (environment varaible) and via the settings page (database), the value from `app.env` takes precedence.
Settings configured in `app.env` cannot be changed or overwridden via the web interface.


### Private Designs
Users without Designer permission can create and edit private designs that cannot be read or used by other users. If a pentest project is created using a private design, a copy of the private design becomes accessible by project members. Use this setting to enable private designs.

``` title="Example:"
ENABLE_PRIVATE_DESIGNS=true
```


### Compress Images
Uploaded images are compressed to reduce file size, but to retain quality suitable for PDF files. Disable image compression using this setting.

``` title="Example:"
COMPRESS_IMAGES=false
```


### PDF Rendering
PDFs are compressed via `ghostscript` when generating the final report (not in previews). 
PDF compression reduces the file size, but can lead to quality loss of images and differences between the preview and the final PDF.
PDF compression is enabled by default. Disable PDF compression using this setting.

``` title="Example:"
COMPRESS_PDFS=false
```

It is possible to generate accessible PDFs in PDF/UA format.
Accessible PDFs can be read by screen readers and are compliant with accessibility standards.
Generating accessible PDFs is incompatible with PDF compression. If you enable accessible PDFs, PDF compression is automatically disabled.

``` title="Example:"
GENERATE_ACCESSIBLE_PDFS=true
```

SysReptor limits the rendering time a PDF can take. If the rendering time exceeds the limit, the PDF render task is aborted. The default limit is 300 seconds (5 minutes).
If you experience slow PDF rendering, try to [optimize your design](../designer/debugging.md#slow-pdf-rendering) before increasing the limit.

``` title="Example:"
PDF_RENDERING_TIME_LIMIT=300
```


### Languages
Configure which languages are available in the language selection.
By default all languages are shown.
When this setting is configured, only selected languages are shown.
All other languages are hidden.

This setting also defines the order of languages in the selection.
The first language is used as default.

``` title="Example:"
PREFERRED_LANGUAGES="de-DE,en-US"
```


### Spell Check
<span style="color:red;">:octicons-heart-fill-24: Pro only</span>

You can add words to the spell check dictionary in the markdown editor (see https://docs.sysreptor.com/reporting/spell-check/).

Words are added to a global spell check dictionary by default, which is available to all users. If words should be added to user's personal spell check dictionaries, set this setting to `true`. 

Using both global and personal dictionaries at the same time is not possible. Words of personal dictionaries are not shared between users. If one user adds an unknown word to their personal dictionary, the spell checker will still detect an error for other users, even when they are working in the same project or finding.


``` title="Spell check dictionary configuration"
SPELLCHECK_DICTIONARY_PER_USER=false
```

The picky mode enables additional spell check rules. 

It is also possible to selectively enable and disable rules or rule-categories by passing a LanguageTool configuration as JSON. 
See https://languagetool.org/http-api/ for available options on the `/check` request.
See https://community.languagetool.org/rule/list for available rules (note: rule IDs might differ for languages).

``` title="Spell check rule configuration"
SPELLCHECK_MODE_PICKY=true
SPELLCHECK_LANGUAGETOOL_CONFIG='{"disabledRules": "TODO,TO_DO_HYPHEN,PASSIVE_VOICE,PASSIVE_SENTENCE_DE"}'
```


### Archiving
<span style="color:red;">:octicons-heart-fill-24: Pro only</span>

Archived projects require at least `ARCHIVING_THRESHOLD` number of users to restore the archive (see https://docs.sysreptor.com/reporting/archiving/). 
By default two users are required, enforcing a 4-eye principle.
If `ARCHIVING_THRESHOLD=1` every user is able to restore archived projects on their own, disabling the 4-eye principle.
Changing this setting does not affect previously archived projects. 

``` title="Example:"
ARCHIVING_THRESHOLD=2
```

If `PROJECT_MEMBERS_CAN_ARCHIVE_PROJECTS` is set to `true` (default), every project member can archive/restore a project.
Otherwise, only users with global archiver permission can archive/restore projects.
This means that encryption happens with fewer encryption keys and it will be more difficult to keep up the quorum (`ARCHIVING_THRESHOLD`) for restoring projects (this could lead to availability problems).

``` title="Example:"
PROJECT_MEMBERS_CAN_ARCHIVE_PROJECTS=false
```

The process of archiving finished projects and deleting old archives can be automated by following settings. The values are time spans in days.

``` title="Example:"
# Automatically archive finished projects after 3 months
AUTOMATICALLY_ARCHIVE_PROJECTS_AFTER=90
# Automatically delete archived projects after 2 years
AUTOMATICALLY_DELETE_ARCHIVED_PROJECTS_AFTER=730
```


### Single Sign-On (SSO)
<span style="color:red;">:octicons-heart-fill-24: Pro only</span>

Configuration for SSO via OIDC. Find detailed instructions at https://docs.sysreptor.com/setup/oidc-setup/.

``` title="OIDC example:"
OIDC_AZURE_TENANT_ID="azure-tenant-id"
OIDC_AZURE_CLIENT_ID="azure-client-id"
OIDC_AZURE_CLIENT_SECRET="azure-client-secret"

OIDC_GOOGLE_CLIENT_ID="google-client-id"
OIDC_GOOGLE_CLIENT_SECRET="google-client-secret"

OIDC_AUTHLIB_OAUTH_CLIENTS='{
    "keycloak": {
        "label": "Keycloak",
        "client_id": "<client-id>",
        "client_secret": "<client-secret>",
        "server_metadata_url": "https://keycloak.example.com/auth/realms/dev/.well-known/openid-configuration",
        "client_kwargs": {
            "scope": "openid email",
            "code_challenge_method": "S256"
        },
        "reauth_supported": false
    }
}'
```

If your reverse proxy enforces authentication and provides the username via a HTTP-Header, use following settings to enable SSO.

``` title="Remote-User example"
REMOTE_USER_AUTH_ENABLED=true
REMOTE_USER_AUTH_HEADER="Remote-User"
```

By default users can decide whether they want to log in via SSO or username/password. It is possible to globally disable login via username/password via this setting.
Make sure all users have SSO identities configured before enabling this option. Else they will not be able to log in anymore.
It is also possible to disable username/password login for specific users via the user management.

``` title="Disable username/password authentication example"
LOCAL_USER_AUTH_ENABLED=false
```

Configuration of the default authentication provider when multiple authentication providers are enabled (e.g. OIDC via Microsoft Entra ID and username/password).
This setting will redirect users to the default authentication provider, skipping the selection. Other authentication providers can still be used if login via the default provider fails.

Possible values: `azure`, `google`, `remoteuser`, `local` (username/password authentication)

``` title="Default authentication provider example"
DEFAULT_AUTH_PROVIDER="azure"
DEFAULT_REAUTH_PROVIDER="local"
```

### Local User Authentication
Local user authentication via username/password is enabled by default. Disable local user authentication to force users to use SSO.

``` title="Example:"
LOCAL_USER_AUTH_ENABLED=true
FORGOT_PASSWORD_ENABLED=false
```

By enabling the `FORGOT_PASSWORD_ENABLED` option, users can reset their passwords themselves via email. This setting only takes effect if `LOCAL_USER_AUTH_ENABLED=true`, email settings are configured, and the user has an email address set. To disable the forgot password functionality for specific users (e.g. superusers), remove the email address from the user profile. Users with superuser or "user manager" permissions are still able to reset passwords in the user management web UI or via the CLI.


### Guest User Permissions
Restrict capabilities of guest users.

``` title="Example:"
GUEST_USERS_CAN_CREATE_PROJECTS=True
GUEST_USERS_CAN_IMPORT_PROJECTS=False
GUEST_USERS_CAN_EDIT_PROJECTS=True
GUEST_USERS_CAN_UPDATE_PROJECT_SETTINGS=True
GUEST_USERS_CAN_DELETE_PROJECTS=True
GUEST_USERS_CAN_SEE_ALL_USERS=False
```

### Custom Statuses
It is possible to define custom statuses for findings and sections. 
In addition to the custom statuses the statuses `in-progress` and `finished` are always available.
By default, the statuses `ready-for-review` and `needs-improvement` are also available.

``` title="Example:"
STATUS_DEFINITIONS='[
  {"id": "ready-for-review", "label": "Ready for review", "icon": "mdi-check"},
  {"id": "needs-improvement", "label": "Needs improvement", "icon": "mdi-exclamation-thick"},
]'
```

It is possible to enforce specific status transition workflows by defining which statuses can follow each status.
This is useful for implementing review processes where certain steps must be followed in order.

Use the `allowed_next_statuses` field to specify which statuses can be set after the current status.
When `allowed_next_statuses` is not defined or an empty list, any status transition is allowed.
To define a terminal status where no further transitions are allowed, set `allowed_next_statuses` to the current status.
Status transitions for built-in statuses (`in-progress`, `finished`) can also be restricted by defining them in `STATUS_DEFINITIONS`.
Please note that `in-progress` is always the initial status and `finished` should be the last status.

``` title="Example: Linear workflow"
STATUS_DEFINITIONS='[
  {"id": "in-progress", "label": "In progress", "icon": "mdi-pencil", "allowed_next_statuses": ["ready-for-review"]},  
  {"id": "ready-for-review", "label": "Ready for review", "icon": "mdi-check", "allowed_next_statuses": ["needs-improvement", "finished"]},
  {"id": "needs-improvement", "label": "Needs improvement", "icon": "mdi-exclamation-thick", "allowed_next_statuses": ["ready-for-review"]},
  {"id": "finished", "label": "Finished", "icon": "mdi-check-all", "allowed_next_statuses": ["finished"]}
]'
```

Note: `allowed_next_statuses` is not enforced for [superusers with enabled admin permissions](/users/user-permissions/#superuser). This is to allow administrators to fix incorrect status assignments if necessary.

