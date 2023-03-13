# Backup

## Create backups
Backups can be created and downloaded via the API.
You can easily created automated backups e.g. once per day via a script.
The downloaded backup archive contains a database export and all uploaded files.

### Configuration
Creating backups is a high-privilege operation, because it essentially contains all data of the application, including sensitive information from users and pentest projects.
Therefore, access to the backup API endpoint is restricted.
Only `system`-users can access this endpoint in combination with a `BACKUP_KEY`.
Neither regular users nor superusers have access to the backup API endpoint.

The `system`-user permission can only be set in the Django admin interface, not via the regular UI.
In order to activate the `system`-user permission to an existing user 
visit `https://sysreptor.example.com/admin/pentestusers/<user-id>/`
and select `is_system`.
This system user should only be used for backups.

Additionally, you need to configure a `BACKUP_KEY` as environment variable.
This backup key has to be at least 20 characters long.
If no `BACKUP_KEY` is configured, the backup API endpoint is disabled.

Optionally, the backup can be encrypted via a 256-bit AES key provided in the HTTP request body.

```
# Create backup
curl -X POST https://sysreptor.example.com/api/v1/utils/backup/ -d '{"key": "<backup-key>"}' -H 'Cookie: sessionid=<session-id>' -o backup.zip

# Create encrypted backup
curl -X POST https://sysreptor.example.com/api/v1/utils/backup/ -d '{"key": "<backup-key>", "aes_key": "<aes-key-as-hex>"}' -H 'Cookie: sessionid=<session-id>' -o backup.zip.crypt
```




# Restore backups
Make sure that you have an empty database and empty data directories (i.e. empty docker volumes), else the old data will be lost.
Make sure that it is the same SysReptor version like the one that was used to create the backup. 
If a different version is used the backup might not be importable, because of a differing database schema.

```bash
# Optionally decrypt backup
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
echo "select 'TRUNCATE "' || tablename || '" RESTART IDENTITY CASCADE;' from pg_tables where schemaname = 'data' and tablename != 'django_migrations';" | docker compose run --no-TTY app python3 manage.py dbshell
cat backup/backup.jsonl | docker compose run --no-TTY app python3 manage.py loaddata --format=jsonl -
```


