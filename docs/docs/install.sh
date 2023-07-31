#!/bin/bash
set -e  # exit on error

echo "Good to see you."
echo "Get ready for the easiest pentest reporting tool."
echo ""

error=1
docker=1
for cmd in curl openssl tar uuidgen docker "docker compose" sed
do
    if
        ! command -v $cmd >/dev/null
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
    test 0 -eq "$docker"
then
    echo "Follow the installation instructions at https://docs.docker.com/engine/install/ubuntu/"
fi
if
    test 0 -eq "$error"
then
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

download_url=https://github.com/syslifters/sysreptor/releases/latest/download/source-prebuilt.tar.gz
echo "Downloading SysReptor from $download_url ..."
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
        echo "deploy/app.env exists. Will not create new secrets."
else
    echo "Creating app.env..."
    cp app.env.example app.env

    echo "Generating secret key..."
    secret_key="SECRET_KEY=\"$(openssl rand -base64 64 | tr -d '\n=')\""
    sed -i'' -e "s#.*SECRET_KEY=.*#$secret_key#" app.env

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
else
    echo "No license key found. Going with Community edition."
fi

echo "Creating docker volumes..."
echo -n "Volume: "
docker volume create sysreptor-db-data
echo -n "Volume: "
docker volume create sysreptor-app-data

echo "Build and launch SysReptor via docker compose..."
echo "We are downloading and installing all dependencies."
echo "This may take a few minutes."

if [ -n "$SYSREPTOR_LICENSE" ]
then
    compose_args=""
else
    compose_args="-f docker-compose.yml"
fi

if
    ! docker compose $compose_args up -d
then
    echo "Ups. Something did not work while bringing up your containers."
    exit -2
fi

echo "Running migrations..."
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
curl -s "$url" | docker compose exec --no-TTY app python3 manage.py importdemodata --type=project --add-member=reptor 2>/dev/null
echo "Importing demo designs..."
url="https://docs.sysreptor.com/assets/demo-designs.tar.gz"
curl -s "$url" | docker compose exec --no-TTY app python3 manage.py importdemodata --type=design 2>/dev/null
echo "Importing finding templates..."
url="https://docs.sysreptor.com/assets/demo-templates.tar.gz"
curl -s "$url" | docker compose exec --no-TTY app python3 manage.py importdemodata --type=template 2>/dev/null
echo "All imported."

echo ""
echo "Very nice."
echo "You can now login at http://127.0.0.1:8000"
echo "Username: reptor"
echo "Password: $password"
echo ""
echo "This was easy, wasn't it?"
echo "We recommend to setup a web server with HTTPS."
echo "Find instructions at: https://docs.sysreptor.com/setup/webserver/"