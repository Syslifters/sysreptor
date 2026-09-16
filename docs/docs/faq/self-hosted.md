# FAQs for self-hosted SysReptor

These FAQs are for operators who install SysReptor with Docker on their own server.

Students writing HTB or OffSec exam reports on [labs.sysre.pt](https://labs.sysre.pt) should use the [exam report FAQs](/faq/exam-reports). SysReptor Cloud is covered in the [cloud FAQs](/faq/cloud).

<FaqExpandAll />

<div class="faq-item">

::: details Can I install SysReptor on macOS or Linux distributions like Kali, Fedora, RHEL?

Even though we officially support **Ubuntu** only, installation is technically possible on most UNIX-based target systems including Kali, Fedora, macOS or RHEL.

The installation of dependencies (like docker, sed, curl, openssl, uuid-runtime, coreutils, cron; some of them are optional) might vary from system to system. Follow the steps for [manual installations](/setup/installation#manual-installation) and adapt the commands according to your system.

If all dependencies are installed and are ready to use, [easy script installation](/setup/installation#easy-script-installation) might also work.
:::

</div>

<div class="faq-item" id="windows">

::: details Can I install SysReptor on Windows?

The easiest approach on Windows is to install SysReptor in [Windows Subsystem for Linux 2](https://learn.microsoft.com/en-us/windows/wsl/install) (WSL 2) with an Ubuntu distribution.

Make sure to install Docker Desktop with WSL 2 and to enable integration of Docker with WSL (in Docker Desktop go to **Settings → Resources → WSL Integration → Enable integration with my default WSL distro**).

:::

</div>


<div class="faq-item">

::: details What are the SysReptor system requirements for a self-hosted install?
For a self-hosted SysReptor server, the requirements are Ubuntu and 8 GB RAM. The application runs in Docker. Details and client browser requirements are in [Installation](/setup/installation).
:::

</div>


<div class="faq-item">

::: details What is the SysReptor default password?
SysReptor has **no fixed default password**.

* The [install script](/setup/installation) creates a superuser named `reptor` and prints a **random password once**. Store it when it is shown; it is not saved in the docs or in a default config file.
* A [manual install](/setup/installation) uses `createsuperuser`, so you choose the username and password yourself.

If you lost the password, reset it from the CLI. From `sysreptor/deploy` run:

```shell
docker compose exec app python3 manage.py changepassword "<username>"
```

Use the username from install (`reptor` if you used the install script). The command prompts twice for a new password, then updates that user. You can log in with the new password immediately.

If no user was created yet, create a superuser from the same directory:

```shell
docker compose exec app python3 manage.py createsuperuser --username "<username>"
```

The command prompts twice for a password. You can log in with that username and password immediately.
:::

</div>


<div class="faq-item" id="uninstall">

::: details How do I cleanly uninstall SysReptor and delete all data?
To uninstall a self-hosted SysReptor and delete all data (database and uploaded files), remove the Docker containers, named volumes, and the install directory.

From the `sysreptor/deploy` directory, stop the stack, then delete containers and volumes:

```shell
cd sysreptor/deploy
docker compose down
docker rm -f sysreptor-app sysreptor-db
docker volume rm -f sysreptor-app-data sysreptor-db-data
```

If you used Caddy from the bundled compose file, also remove `sysreptor-caddy-data`. Then delete the `sysreptor` directory on disk.

This cannot be undone. Create a [backup](/setup/backups) first if you might need the data.

To stop SysReptor **without** deleting data, see [How do I stop SysReptor without deleting data?](#stop-without-deleting).
:::

</div>


<div class="faq-item" id="stop-without-deleting">

::: details How do I stop SysReptor without deleting data?
To stop a self-hosted SysReptor without deleting volumes or files, go to `sysreptor/deploy` and run:

```shell
docker compose stop
```

Your database and uploaded files stay in the Docker volumes.  
To start again: `docker compose up -d`.
:::

</div>


<div class="faq-item" id="verify-integrity">

::: details How do I verify the integrity of a SysReptor installation?
Verify Docker images or the release archive (`setup.tar.gz`) with [cosign](https://docs.sigstore.dev/cosign/system_config/installation/). The SysReptor public key is [https://docs.sysreptor.com/cosign.pub](https://docs.sysreptor.com/cosign.pub).

```shell
SYSREPTOR_VERSION=$(cat sysreptor/deploy/.env | grep 'SYSREPTOR_VERSION=' | cut -d'=' -f2-)
# SYSREPTOR_VERSION=$(docker exec -it sysreptor-app bash -c 'echo "$VERSION"')

# Verify docker images
cosign verify --key https://docs.sysreptor.com/cosign.pub "syslifters/sysreptor:${SYSREPTOR_VERSION}"
cosign verify --key https://docs.sysreptor.com/cosign.pub "syslifters/sysreptor-languagetool:${SYSREPTOR_VERSION}"  # Pro only

# Verify setup.tar.gz
curl -s -L --output sysreptor.tar.gz.sigstore.json https://github.com/Syslifters/sysreptor/releases/download/${SYSREPTOR_VERSION}/setup.tar.gz.sigstore.json
cosign verify-blob sysreptor.tar.gz --key https://docs.sysreptor.com/cosign.pub --bundle sysreptor.tar.gz.sigstore.json
```

`verify-blob` needs the local `sysreptor.tar.gz` you downloaded from GitHub Releases. The same steps are in [Installation](/setup/installation) and [Updates](/setup/updates).
:::

</div>


<div class="faq-item">

::: details How do I update a self-hosted SysReptor?
Update a self-hosted SysReptor with the bundled script (recommended):

```shell
bash sysreptor/update.sh
```

Professional installations can add `--backup` to create a backup before the update. Full steps, manual updates, and image verification are in [Updates](/setup/updates). Create a [backup](/setup/backups) before updating.
:::

</div>


<div class="faq-item">

::: details How do I back up and restore a self-hosted SysReptor instance?
On a self-hosted SysReptor you can back up via CLI, and (with Professional, a superuser, and [`BACKUP_KEY`](/setup/configuration#backup-key)) via the web UI or API. The archive contains all data from your installation, including users, projects, templates, designs, assets, settings, the database export and uploaded files.

CLI example from `sysreptor/deploy`:

```shell
docker compose run --rm app python3 manage.py backup > backup.zip
```

Restore deletes existing data in the database and file storage. Use the same SysReptor version. Full commands: [Backups](/setup/backups#restore-backups).
:::

</div>


<div class="faq-item">

::: details How do I add a SysReptor Professional license to a self-hosted install?
Add your license key to `deploy/app.env` as `LICENSE='your_license_key'`, include the LanguageTool compose file if needed, and run `docker compose up -d` from `deploy`. You do not need to reinstall. No data is lost during the transition from Community to Professional or vice versa.

See [Upgrade to Professional](/setup/upgrade-to-professional) for more details.
:::

</div>


::: info <DocBadge icon="mdi:help-circle" class="lg middle" label="Further questions?" />
Need help or have questions? Get support and [connect with us and the SysReptor community](https://github.com/Syslifters/sysreptor/discussions/).
:::
