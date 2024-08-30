#!/bin/bash
set -e  # exit on error

echo "Good to see you."
echo "Get ready for the easiest pentest reporting tool."
echo ""

error=1
docker=1
for cmd in curl openssl tar uuidgen docker sed
do
    if
        ! command -v "$cmd" >/dev/null
    then
        echo "Error: $cmd is not installed."
        if
            [[ $cmd = docker* ]]
        then
            docker=0
        fi
        error=0
    fi
done
if
    ! docker compose version >/dev/null 2>&1
then
    echo "docker compose v2 is not installed."
    docker=0
    error=0
fi
if
    test 0 -eq "$docker"
then
    echo "Follow the installation instructions at https://docs.docker.com/engine/install/ubuntu/"
    exit -1
fi
if
    test 0 -eq "$error"
then
    echo 'Install dependencies using "apt install -y sed curl openssl uuid-runtime coreutils"'
    exit -1
fi
if
    docker --version | grep podman
then
    echo "Error: You have podman installed. Please install official Docker instead."
    echo "Follow the installation instructions at https://docs.docker.com/engine/install/ubuntu/"
    exit -3
fi

if
    docker volume inspect sysreptor-app-data 1>/dev/null 2>&1 || docker volume inspect sysreptor-db-data 1>/dev/null 2>&1
then
    echo "Old SysReptor volumes exist."
    echo "Remove volumes if you don't need them any more. (This will delete all your data: \"docker rm -f sysreptor-app sysreptor-db && docker volume rm -f sysreptor-app-data sysreptor-db-data\")"
    echo "Want to update instead? See: https://docs.sysreptor.com/setup/updates/"
    exit -4
fi

download_url=https://github.com/syslifters/sysreptor/releases/latest/download/setup.tar.gz
echo "Downloading Docker Compose files from $download_url ..."
curl -s -L --output sysreptor.tar.gz "$download_url"
echo "Checking download..."
if
    ! tar -tzf sysreptor.tar.gz >/dev/null 2>&1
then
    echo "Download did not succeed..."
    exit -5
fi

echo "Unpacking sysreptor.tar.gz..."
tar xzf sysreptor.tar.gz

cd sysreptor/deploy
if
        test -f app.env
then
        echo "deploy/app.env exists. Won't update configuration."
        echo "Find configuration options at https://docs.sysreptor.com/setup/configuration/ for manual editing."
        read -p "Press any key to continue installation..."
        echo ""
else
    if [ ! -n "$SYSREPTOR_LICENSE" ]
    then
        read -p "License key (leave blank for Community Edition; you can upgrade anytime later): " SYSREPTOR_LICENSE
    fi

    while [[ $SYSREPTOR_ENCRYPT != [yY] && $SYSREPTOR_ENCRYPT != [nN] ]]
    do
        read -p "Encrypt files and database? [y/n]: " SYSREPTOR_ENCRYPT
        if [[ $SYSREPTOR_ENCRYPT == [yY] ]]
        then
            echo "We will generate secret keys using OpenSSL and store them in deploy/app.env."
            echo "If you lose this file, your data won't be recoverable."
            read -p "Did you understand that you will lose all data if your app.env is gone? [y/n]: " SYSREPTOR_ENCRYPT
            if [[ $SYSREPTOR_ENCRYPT == [nN] ]]
            then
                echo "All clear, we won't encrypt your stored data."
            fi
        fi
    done

    echo "Creating app.env..."
    cp app.env.example app.env

    echo "Generating Django secret key..."
    secret_key="SECRET_KEY=\"$(openssl rand -base64 64 | tr -d '\n=')\""
    sed -i'' -e "s#.*SECRET_KEY=.*#$secret_key#" app.env

    if [[ $SYSREPTOR_ENCRYPT == [yY] ]]
    then
        echo "Generating data at rest encryption keys..."
        KEY_ID=$(uuidgen)
        encryption_keys="ENCRYPTION_KEYS=[{\"id\": \"${KEY_ID}\", \"key\": \"$(openssl rand -base64 32)\", \"cipher\": \"AES-GCM\", \"revoked\": false}]"
        default_encryption_key_id="DEFAULT_ENCRYPTION_KEY_ID=\"${KEY_ID}\""
        sed -i'' -e "s#.*ENCRYPTION_KEYS=.*#$encryption_keys#" app.env
        sed -i'' -e "s#.*DEFAULT_ENCRYPTION_KEY_ID=.*#$default_encryption_key_id#" app.env
    fi

    if [ -n "$SYSREPTOR_LICENSE" ]
    then
        echo "Adding your license key..."
        sed -i'' -e "s#.*LICENSE=.*#LICENSE='$SYSREPTOR_LICENSE'#" app.env
        
        docker_compose_file="docker-compose.yml"
        include_languagetool="  - languagetool/docker-compose.yml"
        if ! grep -q "^$include_languagetool" "$docker_compose_file"
        then
            echo "Enable languagetool..."
            sed -i "s#include:#include:\n$include_languagetool#" "$docker_compose_file"
        fi
    fi
fi

# Webserver setup (Caddy)
if
    test -f ./caddy/setup.sh
then
    source caddy/setup.sh || true  # do not exit on error
fi

# Delete docker-compose.override.yml because that's needed for existing PRO installations only due to legacy reasons
# ...not for new installations
rm docker-compose.override.yml 2>/dev/null || true

echo "Creating docker volumes..."
echo -n "Volume: "
docker volume create sysreptor-db-data
echo -n "Volume: "
docker volume create sysreptor-app-data

echo "Launching SysReptor via docker compose..."
echo "Downloading the Docker images may take a few minutes."

if
    source .env
    export SYSREPTOR_VERSION
    ! docker compose up -d
then
    echo "Ups. Something did not work while bringing up your containers."
    exit -2
fi

echo ""
echo "Waiting for database setup..."
while
    sleep 1
    ! echo '' | docker compose exec --no-TTY app python3 manage.py migrate --check 1>/dev/null 2>&1
do
    true
done

echo "Great! Everything seems to be up now."
echo ""

echo "Setting up initial data..."
echo "Creating initial user..."
password=`openssl rand -base64 20 | tr -d '\n='`
echo '' | docker compose exec --no-TTY -e DJANGO_SUPERUSER_USERNAME="reptor" -e DJANGO_SUPERUSER_PASSWORD="$password" app python3 manage.py createsuperuser --noinput
echo "Importing demo projects..."
url="https://docs.sysreptor.com/assets/demo-projects.tar.gz"
curl -s "$url" | docker compose exec --no-TTY app python3 manage.py importdemodata --type=project --add-member=reptor
echo "Importing demo designs..."
url="https://docs.sysreptor.com/assets/demo-designs.tar.gz"
curl -s "$url" | docker compose exec --no-TTY app python3 manage.py importdemodata --type=design
echo "Importing finding templates..."
url="https://docs.sysreptor.com/assets/demo-templates.tar.gz"
curl -s "$url" | docker compose exec --no-TTY app python3 manage.py importdemodata --type=template
echo "All imported."

echo ""
echo "Very nice."
if [ -z "$SYSREPTOR_CADDY_PORT" ]
then
    SYSREPTOR_CADDY_PORT=8000
fi
if [ -z "$SYSREPTOR_CADDY_FQDN" ]
then
    echo "You can now login at http://127.0.0.1:$SYSREPTOR_CADDY_PORT"
else
    echo "You can now login at https://$SYSREPTOR_CADDY_FQDN:$SYSREPTOR_CADDY_PORT"
fi
echo "Username: reptor"
echo "Password: $password"

while [[ $CONFIRM != [yY] ]]
do
    read -p "Copy your password now. Copied? [y/n]: " CONFIRM
    if [[ $CONFIRM == [nN] ]]
    then
        echo "It's a good password. You will like it."
    fi
done

if [[ -n "$encryption_keys" && -n "$default_encryption_key_id" ]]
then
    CONFIRM=""
    echo ""
    echo "Those are your encryption keys:"
    echo "$encryption_keys"
    echo "$default_encryption_key_id"
    while [[ $CONFIRM != [yY] ]]
    do
        read -p "Backup your encryption keys now. Done? [y/n]: " CONFIRM
        if [[ $CONFIRM == [nN] ]]
        then
            echo "Not your keys, not your data. Backup them!"
        fi
    done
fi

echo ""
echo "This was easy, wasn't it?"
