## Prerequisites
### Server
:octicons-server-24: Self-Hosted

* Ubuntu
* 4GB RAM
* Latest [Docker](https://docs.docker.com/engine/install/ubuntu/){ target=_blank } (with docker-compose-plugin)

### Client
:octicons-cloud-24: Cloud · :octicons-server-24: Self-Hosted

* Network connection to the server
* Up-to-date desktop browser, one of:
    * Chrome
    * Edge
    * Firefox
    * Safari


## Installation
:octicons-server-24: Self-Hosted

=== "Easy Script Installation"
    
    Installation via script is the easiest option. You need (official) [Docker](https://docs.docker.com/engine/install/ubuntu/){ target=_blank }  installed.

    Install additional requirements:
    ```shell
    sudo apt update
    sudo apt install -y sed curl openssl uuid-runtime coreutils
    ```

    The user running the installation script must have the permission to use docker.  
    Download and run:

    ```shell
    curl -s https://docs.sysreptor.com/install.sh | bash
    ```

    The installation script creates a new `sysreptor` directory holding the source code and everything you need.  
    It will build a docker image, create volumes and secrets and bring up your containers.

=== "Manual Installation"

    You need (official) [Docker](https://docs.docker.com/engine/install/ubuntu/){ target=_blank }  installed.

    Download and extract the latest SysReptor release:
    ```shell
    curl -s -L --output sysreptor.tar.gz https://github.com/syslifters/sysreptor/releases/latest/download/source-prebuilt.tar.gz
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

    Build Docker image and run container from the `deploy` directory:

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

Access your application at http://127.0.0.1:8000/.

We recommend [using a webserver](../setup/webserver.md) like Caddy (recommended), nginx or Apache to prevent [potential vulnerabilities](../insights/vulnerabilities.md) and to enable HTTPS.

Further [configurations](../setup/configuration.md) can be edited in `sysreptor/deploy/app.env`.
