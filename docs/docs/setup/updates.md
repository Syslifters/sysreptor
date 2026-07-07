# Updates

<BadgeSelfHosted />

We recommend to create a [backup](/setup/backups) of your installation before updating.


::: tabs
== Update via Script (recommended)

We deliver the shell script `update.sh` in the `sysreptor` directory.

If updates are available, the script downloads the release from GitHub. It replaces your Docker images by the newest release and restarts all containers.  

Your current SysReptor directory will be renamed for backup purposes. The script will download the newer version and place it into the directory where the old version was.

It will then copy your `app.env`, `.env`, `docker-compose.yml` and if present the `Caddyfile` to the correct locations of your newer version. The new SysReptor version launched and the docker images of your old verions are cleaned up.

```shell title="Run update script:"
bash sysreptor/update.sh
```

<BadgePro />

Using the `--backup` switch, a SysReptor backup will be created prior to the update. The update will fail if the backup fails.

```shell title="Run update script:"
bash sysreptor/update.sh --backup
```

Please make sure to monitor your disk space and clean up old backups, as automatic backups might increase disk usage significantly.

== Manual update

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

:::

::: details Optional: Verify docker images
```shell
SYSREPTOR_VERSION=$(cat sysreptor/deploy/.env | grep 'SYSREPTOR_VERSION=' | cut -d'=' -f2-)

# Verify setup.tar.gz
curl -s -L --output sysreptor.tar.gz.sigstore.json https://github.com/syslifters/sysreptor/releases/${SYSREPTOR_VERSION}/download/setup.tar.gz.sigstore.json
cosign verify-blob sysreptor.tar.gz --key https://docs.sysreptor.com/cosign.pub --bundle sysreptor.tar.gz.sigstore.json

# Verify docker images
cosign verify --key https://docs.sysreptor.com/cosign.pub "syslifters/sysreptor:${SYSREPTOR_VERSION}"
cosign verify --key https://docs.sysreptor.com/cosign.pub "syslifters/sysreptor-languagetool:${SYSREPTOR_VERSION}"  # Pro only
```
:::

Find instructions how to [downgrade](/setup/downgrades) to previous versions.


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
0 0 * * * /bin/bash /home/yourpath/sysreptor/update.sh  # Optional (pro only): --backup
```

Make sure your user has write permissions to the parent directory of your SysReptor directory. In this example, you need write permissions to `/home/yourpath/`.
