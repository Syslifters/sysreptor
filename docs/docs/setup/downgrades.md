# Downgrades
:octicons-server-24: Self-Hosted

<span style="color:red;">:octicons-heart-fill-24: Pro only</span>

!!! info

    Downgrading requires a backup from the version that you want downgrade to.


1. Create a backup

Create a [backup](backups.md) before downgrading.

2. Change directory to your previous version

The update script creates a backup of your prior version's configuration. The directory is usually named `sysreptor-backup-<date>`.  
Enter the `deploy` directory within that folder.

```bash
cd sysreptor-backup-<date>/deploy
```

3. Restore the backup

```bash
cat <your-backup-file>.zip | docker compose run --rm --no-TTY app python3 manage.py restorebackup
```

!!! warning

    This command deletes all present data an restores data from the backup.
    Do not run without having made a backup.


4. Launch the old SysReptor version

```bash
docker compose up -d
```
