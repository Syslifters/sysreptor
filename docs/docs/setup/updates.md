# Updates

:octicons-server-24: Self-Hosted

We recommend to create a [backup](/backups/) of your installation before updating.

=== "Update via Script (recommended)"
    We deliver the shell script `update.sh` in the `sysreptor` directory.

    If updates are available, the script downloads the release from GitHub. It rebuilds your Docker images and restarts all containers.  
    If no updates are available, the script checks when the Docker images were last built. If the last build date was more then seven days ago, the Docker images are rebuilt to ensure that all base images and dependencies are up to date.

    Use the `--force` option to force rebuilding the Docker images.

    Your current SysReptor directory will be renamed for backup purposes. The script will download the newer version and place it into the directory where the old version was.

    It will then copy your `app.env` to the right location of your newer version. The new docker images are build and launched.

    ```shell title="Run update script:"
    bash sysreptor/update.sh
    ```

=== "Manual update"
    Download and extract the latest SysReptor release:
    ```shell
    curl -s -L --output sysreptor.tar.gz https://github.com/syslifters/sysreptor/releases/latest/download/source-prebuilt.tar.gz
    tar xzf sysreptor.tar.gz
    ```

    Copy `deploy/app.env` from your old installation to the new installation.

    `cd` to `sysreptor/deploy`. Then, build Docker images and launch containers:
    ```shell title="Community:"
    docker compose -f docker-compose.yml up -d --build
    ```

    ```shell title="Professional:"
    docker compose up -d --build
    ```
    

## Recommended: Automatic updates
We recommend to deploy automatic updates and run the script once per day. This ensures you receive updates early and you regularly update all dependencies and base images.

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
