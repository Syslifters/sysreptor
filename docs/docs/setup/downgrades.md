# Downgrades
<BadgeSelfHosted />

<BadgePro />


::: info


Downgrading requires a backup from the version that you want downgrade to.

:::

1. Create a backup

Create a [backup](/setup/backups) before downgrading.

2. Change directory to your previous version

The update script creates a backup of your prior version's configuration. The directory is usually named `sysreptor-backup-<date>`.  
Enter the `deploy` directory within that folder.

```shell
cd sysreptor-backup-<date>/deploy
```

3. Restore the backup

```shell
cat <your-backup-file>.zip | docker compose run --rm --no-TTY app python3 manage.py restorebackup
```


::: warning


This command deletes all present data and restores data from the backup.
Do not run without having made a backup.

:::

4. Launch the old SysReptor version

```shell
docker compose up -d
```
