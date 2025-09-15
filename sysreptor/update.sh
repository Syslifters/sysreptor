#!/usr/bin/env bash
set -e  # exit on error
error_cleanup() {
    if
        [ "$created_backup" == "1" ]
    then
        set +e
        echo cd "$script_location"
        echo "Trying to restore your old version..."
        cd `dirname "$script_location"`
        mv "$sysreptor_directory" "$sysreptor_directory-failed-update-$filename_date"
        mv "$backup_copy" "$sysreptor_directory"
        cd "$sysreptor_directory"/deploy
        source .env
        export SYSREPTOR_VERSION=$OLD_SYSREPTOR_VERSION
        docker compose up -d
        echo "An error happened during installation."
        exit -3
    fi
    exit -4
}
filename_date=$(date -Iseconds)
script_location="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
sysreptor_directory=${script_location##*/}
backup_copy="$sysreptor_directory-backup-$filename_date"

trap 'error_cleanup' ERR INT
echo "Easy update of SysReptor"
echo ""

# Check if required commands are installed
error=1
for cmd in curl tar docker date grep realpath dirname
do
    if
        ! command -v "$cmd" >/dev/null
    then
        echo "Error: $cmd is not installed."
        error=0
    fi
done
if 
    ! docker compose version >/dev/null 2>&1
then
    echo "docker compose v2 is not installed."
    error=0
fi
if
    test 0 -eq "$error"
then
    exit -1
fi
# cd to script location
cd "$script_location"
# check if parent directory writable
if
    ! test -w ..
then
    echo "\"`readlink -e ..`\" not writeable. Exiting..."
    exit -2
fi

# Parse CLI arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --backup)
      BACKUP_LOCATION=`realpath "$script_location/../sysreptor-full-backup-$filename_date.zip"`
      shift
      ;;
    -*|--*)
      echo "$1 is not a valid option."
      exit -7
      ;;
    *)
      # Positional arguments (not processed)
      shift
      ;;
  esac
done

DOWNLOAD_URL=https://github.com/syslifters/sysreptor/releases/latest/download/setup.tar.gz
DOCKER_HUB_IMAGE=syslifters/sysreptor
DOCKER_HUB_LANGUAGETOOL_IMAGE=syslifters/sysreptor-languagetool

source deploy/.env
OLD_SYSREPTOR_VERSION=$SYSREPTOR_VERSION
echo "Your current version is $OLD_SYSREPTOR_VERSION"

echo "Checking if update is available..."
version=`curl -s https://docs.sysreptor.com/latest.version`
if ! [[ $version =~ ^[0-9]{4}\.[0-9]+$ ]]
then
    echo "Checking for new version failed."
    exit -6
fi
if [ "$version" != "$OLD_SYSREPTOR_VERSION" ]
then
    echo "Found newer version $version"
else
    echo "The latest SysReptor version is already installed."
    exit 0
fi
NEW_SYSREPTOR_VERSION=$version

if [ -n "$BACKUP_LOCATION" ]; then
    cd "$script_location"
    echo ""
    echo "Creating full backup of your current installation..."
    if
        docker compose -f deploy/docker-compose.yml exec -it app python3 manage.py backup > "$BACKUP_LOCATION" 2>/dev/null
    then
        echo "Backup written to $BACKUP_LOCATION"
        echo ""
    else
        echo "Backup failed. Exiting..."
        exit -9
    fi
fi

echo "Downloading SysReptor from $DOWNLOAD_URL ..."
curl -s -L --output ../sysreptor.tar.gz "$DOWNLOAD_URL"
echo "Checking download..."
if ! tar -tzf ../sysreptor.tar.gz >/dev/null 2>&1
then
    echo "Download did not succeed..."
    exit -5
fi

echo "Creating copy of your config files..."
cd ..
mv "$sysreptor_directory" "$backup_copy"
created_backup=1
echo "Config backup located at $backup_copy"

echo "Unpacking sysreptor.tar.gz..."
mkdir "$sysreptor_directory"
tar xzf sysreptor.tar.gz -C "$sysreptor_directory" --strip-components=1
echo "Copying your config files app.env and .env..."
source "${sysreptor_directory}/deploy/.env"  # get new SYSREPTOR_VERSION
NEW_SYSREPTOR_VERSION=$SYSREPTOR_VERSION
cp "${backup_copy}/deploy/app.env" "${sysreptor_directory}/deploy/app.env"
grep -v "^SYSREPTOR_VERSION=" "${backup_copy}/deploy/.env" > "${sysreptor_directory}/deploy/.env"
sed -i "1s/^/SYSREPTOR_VERSION=${NEW_SYSREPTOR_VERSION}\n/" "${sysreptor_directory}/deploy/.env"

if grep "sysreptor/docker-compose.yml" "${backup_copy}/deploy/docker-compose.yml" >/dev/null 2>&1
then
    # Copy docker-compose.yml if it is not the old version (2024.58 and earlier)
    echo "Copying your docker-compose.yml..."
    cp "${backup_copy}/deploy/docker-compose.yml" "${sysreptor_directory}/deploy/docker-compose.yml"
fi
if [ -f "${backup_copy}/deploy/caddy/Caddyfile" ]; then
    echo "Copying Caddyfile..."
    cp "${backup_copy}/deploy/caddy/Caddyfile" "${sysreptor_directory}/deploy/caddy/Caddyfile"
fi
echo "Launching SysReptor via docker compose..."
echo "Downloading the Docker images may take a few minutes."

# Remove deprecated docker-compose.override.yml which is there for legacy reasons
rm "${sysreptor_directory}/deploy/docker-compose.override.yml" 2>/dev/null || true
if grep "^LICENSE=" "${sysreptor_directory}/deploy/app.env" >/dev/null 2>&1
then
    # This if-statement will be removed July 2025
    include_languagetool="  - languagetool/docker-compose.yml"
    if ! grep -q "^$include_languagetool" "${sysreptor_directory}/deploy/docker-compose.yml" >/dev/null 2>&1
    then
        # Include languagetool in docker-compose.yml
        sed -i "s#include:#include:\n$include_languagetool#" "${sysreptor_directory}/deploy/docker-compose.yml"
    fi
fi
if
    cd "$sysreptor_directory"/deploy
    source .env
    export SYSREPTOR_VERSION=$NEW_SYSREPTOR_VERSION
    ! docker compose up -d
then
    echo "Ups. Something did not work while building and launching your containers."
fi

echo "Cleaning up your old docker images..."
for image in $DOCKER_HUB_IMAGE $DOCKER_HUB_LANGUAGETOOL_IMAGE; do
    docker rmi "$image:$OLD_SYSREPTOR_VERSION" 2>/dev/null || true
done

echo "Nice. Successfully updated."
echo "Easy peasy lemon squeezy."
