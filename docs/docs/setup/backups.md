# Backups
<BadgePro />


## Create backups via CLI
<BadgeSelfHosted />

Backups can be created via a CLI command or an API request.
The backup archive contains a database export and all uploaded files.

Execute following command to create a backup:
```shell title="Create backup via CLI"
docker compose run --rm app python3 manage.py backup > backup.zip
```

Backups can be encrypted using a 256-bit AES key. 
Specify the key as hex string via the `--key` CLI argument.
```shell title="Create encrypted backup via CLI"
docker compose run --rm app python3 manage.py backup --key "<aes-key-as-hex>" > backup.zip.crypt
```

## Create a backup during update
When [updating](/setup/updates) SysReptor, you can use the `--backup` switch, which will create a backup before applying the update.

## Create backups via web interface
<BadgeCloud /> · <BadgeSelfHosted />

Users with [`superuser` permissions](/users/user-permissions#superuser) and access to the [`BACKUP_KEY`](/setup/configuration#backup-key) can create backups using the web interface.

If no [`BACKUP_KEY`](/setup/configuration#backup-key) is configured, you cannot create backups via the web interface.

## Create backups via API
<BadgeCloud /> · <BadgeSelfHosted />

Users with [`superuser` permissions](/users/user-permissions#superuser) and [`system` users](/users/user-permissions#system) can [create backups via the API](https://demo.sysre.pt/api/public/utils/swagger-ui/#/v1/v1_utils_backup_create) in combination with the configured [`BACKUP_KEY`](/setup/configuration#backup-key).

If no `BACKUP_KEY` is configured, the backup API endpoint is disabled.

The backup can optionally be encrypted via a 256-bit AES key provided in the HTTP request body or pushed to an S3 bucket (see [API parameters](https://demo.sysre.pt/api/public/utils/swagger-ui/#/v1/v1_utils_backup_create)).

### API Requests
```
# Create backup
curl -X POST https://sysreptor.example.com/api/v1/utils/backup/ -d '{"key": "<backup-key>"}' -H 'Authorization: Bearer <api-token>' -H "Content-Type: application/json" -o backup.zip

# Create encrypted backup
curl -X POST https://sysreptor.example.com/api/v1/utils/backup/ -d '{"key": "<backup-key>", "aes_key": "<aes-key-as-base64>"}' -H 'Authorization: Bearer <api-token>' -H "Content-Type: application/json" -o backup.zip.crypt
```

## Restore backups
<BadgeSelfHosted />

Make sure that you have an empty database and empty data directories (i.e. empty docker volumes). Otherwise, you will **lose your old data**.
During the backup restore, all existing data in the database and file storages is deleted.

It is recommended to import the backup into the same SysReptor version like the one that was used to create the backup.
If a different version is used the database schema might not be compatible.

```shell title="Restore backup via CLI"
cat backup.zip | docker compose run --rm --no-TTY app python3 manage.py restorebackup
```

Encrypted backups can be restored as well. Specify the AES key as hex string via the `--key` CLI argument.
```shell title="Restore encrypted backup via CLI"
cat backup.zip.crypt | docker compose run --rm --no-TTY app python3 manage.py restorebackup --key "<aes-key-as-hex>"
```
