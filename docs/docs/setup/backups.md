# Backups
<span style="color:red;">:octicons-heart-fill-24: Pro only</span>

## Create backups
Create backups via REST API. The backup archive contains a database export and all uploaded files.

### Prerequisites
Creating backups is a high-privilege operation. Therefore, access to the backup API endpoint is restricted.
Only [`system`-users](/setup/user-permissions/#system) can access this endpoint in combination with a `BACKUP_KEY`.
Neither regular users nor superusers have access to the backup API endpoint.

Additionally, you need to configure a `BACKUP_KEY` as environment variable.
This backup key has to be at least 20 characters long.
If no `BACKUP_KEY` is configured, the backup API endpoint is disabled.

Optionally, the backup can be encrypted via a 256-bit AES key provided in the HTTP request body.

### API Requests
```
# Create backup
curl -X POST https://sysreptor.example.com/api/v1/utils/backup/ -d '{"key": "<backup-key>"}' -H 'Cookie: sessionid=<session-id>' -H "Content-Type: application/json" -o backup.zip

# Create encrypted backup
curl -X POST https://sysreptor.example.com/api/v1/utils/backup/ -d '{"key": "<backup-key>", "aes_key": "<aes-key-as-hex>"}' -H 'Cookie: sessionid=<session-id>' -H "Content-Type: application/json" -o backup.zip.crypt
```

## Restore backups
Make sure that you have an empty database and empty data directories (i.e. empty docker volumes). Otherwise, you will **lose your old data**.

Make sure that it is the same SysReptor version like the one that was used to create the backup. 
If a different version is used the backup might not be importable, because of a differing database schema.

```bash
cd deploy

# Optionally decrypt backup using your AES key

# Unpack backup
unzip backup.zip -d backup

# Restore files
docker compose up -d
docker compose cp backup/uploadedassets app:/data/
docker compose cp backup/uploadedimages app:/data/
docker compose cp backup/uploadedfiles app:/data/
docker compose down

# Restore database
docker compose run app python3 manage.py flush --no-input
docker compose run app python3 manage.py migrate
echo "select 'TRUNCATE \"' || tablename || '\" RESTART IDENTITY CASCADE;' from pg_tables where schemaname = 'public' and tablename != 'django_migrations';" | docker compose run --no-TTY app python3 manage.py dbshell -- -t | docker compose run --no-TTY app python3 manage.py dbshell
cat backup/backup.jsonl | docker compose run --no-TTY app python3 manage.py loaddata --format=jsonl -
```
