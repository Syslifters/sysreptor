# Configuration
`app.env` (located in `deploy` directory) controls the behaviour of your SysReptor installation.  

After making changes, go to `sysreptor/deploy` and restart the containers:

=== "Professional"
    ```shell
    docker compose up -d
    ```

=== "Community"
    ```shell
    docker compose -f docker-compose.yml up -d
    ```


:octicons-cloud-24: Cloud · We take care of all configurations. If you want to change anything, please [contact us](/contact-us/){ target=_blank }.

## Avaliable Options
:octicons-server-24: Self-Hosted

### Django Secret Key
Django server secret key (see https://docs.djangoproject.com/en/4.1/ref/settings/#std-setting-SECRET_KEY).
Make sure this key remains secret.

``` title="Generate random secret key:"
printf "SECRET_KEY=$(openssl rand -base64 64 | tr -d '\n=')\n"
```

``` title="Example (regenerate this value!):"
SECRET_KEY="TODO-change-me-Z6cuMithzO0fMn3ZqJ7nTg0YJznoHiJXoJCNngQM4Kqzzd3fiYKdVx9ZidvTzqsm"
```

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

### Single Sign-On (SSO)
<span style="color:red;">:octicons-heart-fill-24: Pro only</span>

Configuration for SSO via OIDC. Find detailed instructions at https://docs.sysreptor.com/setup/oidc-setup/.

``` title="OIDC example:"
OIDC_AZURE_TENANT_ID="azure-tenant-id"
OIDC_AZURE_CLIENT_ID="azure-client-id"
OIDC_AZURE_CLIENT_SECRET="azure-client-secret"

OIDC_GOOGLE_CLIENT_ID="google-client-id"
OIDC_GOOGLE_CLIENT_SECRET="google-client-secret"
```

If your reverse proxy enforces authentication and provides the username via a HTTP-Header, use following settings to enable SSO.

``` title="Remote-User example"
REMOTE_USER_AUTH_ENABLED=true
REMOTE_USER_AUTH_HEADER="Remote-User"
```

By default users can decide whether they want to log in via SSO or username/password. It is possible to disable login via username/password.
Make sure all users have SSO identities configured before enabling this option. Else they will not be able to log in anymore.

``` title="Disable username/password authentication example"
LOCAL_USER_AUTH_ENABLED=false
```

Configuration of the default authentication provider when multiple authentication providers are enabled (e.g. OIDC via Azure AD and username/password).
This setting will redirect users to the default authentication provider, skipping the selection. Other authentication providers can still be used if login via the default provider fails.

Possible values: `azure`, `google`, `remoteuser`, `local` (username/password authentication)

``` title="Default authentication provider example"
DEFAULT_AUTH_PROVIDER="azure"
DEFAULT_REAUTH_PROVIDER="local"
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


### Archiving
<span style="color:red;">:octicons-heart-fill-24: Pro only</span>

Archived projects require at least `ARCHIVING_THRESHOLD` number of users to restore the archive (see https://docs.sysreptor.com/reporting/archiving/). 
By default two users are required, enforcing a 4-eye principle.
If `ARCHIVING_THRESHOLD=1` every user is able to restore archived projects on their own, disabling the 4-eye principle.
Changing this setting does not affect previously archived projects. 

``` title="Example:"
ARCHIVING_THRESHOLD=2
```

The process of archiving finished projects and deleting old archives can be automated by following settings. The values are time spans in days.

``` title="Example:"
# Automatically archive finished projects after 3 months
AUTOMATICALLY_ARCHIVE_PROJECTS_AFTER=90
# Automatically delete archived projects after 2 years
AUTOMATICALLY_DELETE_ARCHIVED_PROJECTS_AFTER=730
```



### Private Designs
Users without Designer permission can create and edit private designs that cannot be read or used by other users. If a pentest project is created using a private design, a copy of the private design becomes accessible by project members. Use this setting to enable private designs.

``` title="Example:"
ENABLE_PRIVATE_DESIGNS=true
```

### Guest Users
Restrict capabilities of guest users.

``` title="Example:"
GUEST_USERS_CAN_CREATE_PROJECTS=True
GUEST_USERS_CAN_IMPORT_PROJECTS=False
GUEST_USERS_CAN_UPDATE_PROJECT_SETTINGS=True
GUEST_USERS_CAN_DELETE_PROJECTS=True
```

### S3 Storage
Uploaded files (~~except images~~, images are also encrypted) in notes can be uploaded to an S3 bucket. Files are stored on the filesystem in a docker volume by default. If data at rest encryption is configured files are encrypted.

``` title="Example:"
UPLOADED_FILE_STORAGE="s3"  # Default: "filesystem"
UPLOADED_FILE_S3_ACCESS_KEY="access-key"
UPLOADED_FILE_S3_SECRET_KEY="secret-key"
UPLOADED_FILE_S3_SESSION_TOKEN="session-token"  # optional
UPLOADED_FILE_S3_BUCKET_NAME="bucket-name"
UPLOADED_FILE_S3_ENDPOINT_URL="endpoint-url"
```

Archived project files can also be uploaded to an S3 bucket. Archives are stored on the filesystem in a docker volume by default.

``` title="Example"
ARCHIVED_FILE_STORAGE="s3"  # Default: "filesystem"
ARCHIVED_FILE_S3_ACCESS_KEY="access-key"
ARCHIVED_FILE_S3_SECRET_KEY="secret-key"
ARCHIVED_FILE_S3_SESSION_TOKEN="session-token"  # optional
ARCHIVED_FILE_S3_BUCKET_NAME="bucket-name"
ARCHIVED_FILE_S3_ENDPOINT_URL="endpoint-url"
```


### Backup Key
<span style="color:red;">:octicons-heart-fill-24: Pro only</span>

API key used for creating backups via REST API. The key should be random and must have 20 or more characters. Find more information at https://docs.sysreptor.com/backups/.  
Make sure this key remains secret.

``` title="Generate random backup key:"
printf "BACKUP_KEY=$(openssl rand -base64 25 | tr -d '\n=')\n"
```

``` title="Example (do not use this value!):"
BACKUP_KEY="WfyqYzRVZAOFbCtltYEFN36XBzRz6Ys6ZA"
```

### Compress Images
Uploaded images are compressed to reduce file size, but to retain quality suitable for PDF files. Disable image compression using this setting.

``` title="Example:"
COMPRESS_IMAGES=false
```


### Reverse Proxy
Interpret `X-Forwared-*` headers when SysReptor is behind a reverse proxy. 
See also https://docs.djangoproject.com/en/stable/ref/settings/#use-x-forwarded-host

```
USE_X_FORWARDED_HOST=on
USE_X_FORWARDED_PORT=on
```
