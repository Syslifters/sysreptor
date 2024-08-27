# Updates

:octicons-server-24: Self-Hosted

We recommend to create a [backup](backups.md) of your installation before updating.

=== "Update via Script (recommended)"
    We deliver the shell script `update.sh` in the `sysreptor` directory.

    If updates are available, the script downloads the release from GitHub. It replaces your Docker images by the newest release and restarts all containers.  

    Your current SysReptor directory will be renamed for backup purposes. The script will download the newer version and place it into the directory where the old version was.

    It will then copy your `app.env`, `.env`, `docker-compose.yml` and if present the `Caddyfile` to the correct locations of your newer version. The new SysReptor version launched and the docker images of your old verions are cleaned up.

    ```shell title="Run update script:"
    bash sysreptor/update.sh
    ```

=== "Manual update"
    Download and extract the latest SysReptor release:
    ```shell
    curl -s -L --output sysreptor.tar.gz https://github.com/syslifters/sysreptor/releases/latest/download/setup.tar.gz
    tar xzf sysreptor.tar.gz
    ```

    Copy the following files from your old installation to the new installation.
     * `deploy/app.env`
     * `deploy/docker-compose.yml`
     * `deploy/caddy/Caddyfile` (optional, if present)

    Copy the contents of your `deploy/.env` file to the new installation. Make sure to keep the new version number intact and don't replace it by the old version number.

    `cd` to `sysreptor/deploy` and launch the containers:

    ```shell
    docker compose up -d
    ```
    

## Recommended: Automatic updates
We recommend to deploy automatic updates and run the script once per day. This ensures you receive updates early.

If `cron` is not installed, install and start:
```shell
sudo apt update
sudo apt install -y cron
sudo systemctl start cron
#sudo /etc/init.d/cron start
```

Open `crontab`:
```shell
crontab -e
```

Schedule your update, e.g. every day at midnight:
```shell
0 0 * * * /bin/bash /home/yourpath/sysreptor/update.sh
```

Make sure your user has write permissions to the parent directory of your SysReptor directory. In this example, you need write permissions to `/home/yourpath/`.
