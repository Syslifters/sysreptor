<BadgeSelfHosted />


::: details System Requirements

### Server
<BadgeSelfHosted />

* Ubuntu[^1]
* 8GB RAM

[^1]: It may also run on [Kali](https://emvee-nl.github.io/posts/SysReptor/), [MacOS](https://alive-club-f8d.notion.site/Sysreptor-Install-M2-Studio-12e1fd44f31080a28acae6de346c6a30), RHEL, and more as long as you take care of all dependencies. Our install and update procedures, however, focus on Ubuntu.

### Client
<BadgeCloud /> · <BadgeSelfHosted />

* Network connection to the server
* Up-to-date desktop browser, one of:
    * Chrome
    * Edge
    * Firefox
    * Safari

:::


::: tabs
== Easy Script Installation


Installation via script is the easiest option.

Install additonal requirements:
```shell
sudo apt update
sudo apt install -y sed curl openssl uuid-runtime coreutils
```

Install Docker:
```shell
curl -fsSL https://get.docker.com | sudo bash
```

Make sure your user is allowed to use Docker. For this, you can add your user to the docker group:

```shell
sudo groupadd docker 2>/dev/null  # Creates the Docker group if it doesn't exist
sudo usermod -aG docker $USER  # Add the current user to the Docker group
newgrp docker  # Instantly apply the group membership
```

Download the SysReptor install script and run:

```shell
bash <(curl -s https://docs.sysreptor.com/install.sh)
```

The installation script creates a new `sysreptor` directory holding the source code and everything you need.  
It will set up all configurations, create volumes and secrets, download images from Docker hub and bring up your containers.

== Manual Installation


Install Docker:
```shell
curl -fsSL https://get.docker.com | sudo bash
```

Make sure your user is allowed to use Docker. For this, you can add your user to the docker group:

```shell
sudo groupadd docker 2>/dev/null  # Creates the Docker group if it doesn't exist
sudo usermod -aG docker $USER  # Add the current user to the Docker group
newgrp docker  # Instantly apply the group membership
```

Download and extract the latest SysReptor setup files:

```shell
curl -s -L --output sysreptor.tar.gz https://github.com/syslifters/sysreptor/releases/latest/download/setup.tar.gz
tar xzf sysreptor.tar.gz
```

Create your `app.env`:
```shell
cd sysreptor/deploy
cp app.env.example app.env
```

Generate Django secret key and add to `app.env`:
```shell
printf "SECRET_KEY=\"$(openssl rand -base64 64 | tr -d '\n=')\"\n"
```

Optional: If you want to encrypt sensitive data at rest (data in the database and uploaded files and images), generate encryption keys and add to `app.env`:
```shell
KEY_ID=$(uuidgen) && printf "ENCRYPTION_KEYS=[{\"id\": \"${KEY_ID}\", \"key\": \"$(openssl rand -base64 32)\", \"cipher\": \"AES-GCM\", \"revoked\": false}]\nDEFAULT_ENCRYPTION_KEY_ID=\"${KEY_ID}\"\n"
```

Optional: Add Professional license key to `app.env`:
```
LICENSE="<your license key>"
```

Optional: Professional installations need an additional docker container for the spell check. Add `languagetool/docker-compose.yml` to `docker-compose.yml` in the `deploy` directory:
```
name: sysreptor

include:
  - sysreptor/docker-compose.yml
  - languagetool/docker-compose.yml
```

Create docker volumes:
```shell
docker volume create sysreptor-db-data
docker volume create sysreptor-app-data
```

Launch containers (from the `deploy` directory):

```shell
docker compose up -d
```

Add initial superuser:
```shell
username=reptor
docker compose exec app python3 manage.py createsuperuser --username "$username"
```

Add demo data:
```
# Projects
url="https://docs.sysreptor.com/assets/demo-projects.tar.gz"
curl -s "$url" | docker compose exec --no-TTY app python3 manage.py importdemodata --type=project --add-member="$username"

# Designs
url="https://docs.sysreptor.com/assets/demo-designs.tar.gz"
curl -s "$url" | docker compose exec --no-TTY app python3 manage.py importdemodata --type=design

# Finding templates
url="https://docs.sysreptor.com/assets/demo-templates.tar.gz"
curl -s "$url" | docker compose exec --no-TTY app python3 manage.py importdemodata --type=template
```

:::

::: details Optional: Verify docker images
```shell
SYSREPTOR_VERSION=$(cat sysreptor/deploy/.env | grep 'SYSREPTOR_VERSION=' | cut -d'=' -f2-)
# SYSREPTOR_VERSION=$(docker exec -it sysreptor-app bash -c 'echo "$VERSION"')

# Verify setup.tar.gz
curl -s -L --output sysreptor.tar.gz.sigstore.json https://github.com/syslifters/sysreptor/releases/${SYSREPTOR_VERSION}/download/setup.tar.gz.sigstore.json
cosign verify-blob sysreptor.tar.gz --key https://docs.sysreptor.com/cosign.pub --bundle sysreptor.tar.gz.sigstore.json

# Verify docker images
cosign verify --key https://docs.sysreptor.com/cosign.pub "syslifters/sysreptor:${SYSREPTOR_VERSION}"
cosign verify --key https://docs.sysreptor.com/cosign.pub "syslifters/sysreptor-languagetool:${SYSREPTOR_VERSION}"  # Pro only
```
:::

Access your application at http://127.0.0.1:8000/.

We recommend [using a webserver](/setup/webserver) like Caddy (recommended), nginx or Apache to prevent [potential vulnerabilities](https://github.com/Syslifters/sysreptor/security/advisories) and to enable HTTPS.

Further [configurations](/setup/configuration) can be edited in `sysreptor/deploy/app.env`.

## Stopping SysReptor

To stop SysReptor and all associated containers, go to the `sysreptor/deploy` directory and run `docker compose stop`.

::: info <DocBadge icon="mdi:help-circle" class="lg middle" label="Further questions?" />

Need help or have questions? Get support and connect with us and the SysReptor community.

[Get help](https://github.com/Syslifters/sysreptor/discussions/categories/q-a)

:::