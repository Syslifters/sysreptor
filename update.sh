    #!/bin/bash
    set -e  # exit on error
    error_cleanup() {
        if
            [ "$created_backup" == "1" ]
        then
            set +e
            echo cd "$script_location"
            echo "Trying to restore your old version..."
            cd `dirname "$script_location"`
            mv "$sysreptor_directory" "$sysreptor_directory"-failed-update-$(date +"%Y-%m-%d-%X")
            mv "$backup_copy" "$sysreptor_directory"
            cd "$sysreptor_directory"/deploy
            docker compose up -d
            echo "Error failed during installation."
            exit -3
        fi
        exit -4
    }
    trap 'error_cleanup' ERR


    echo "Easy update of SysReptor"
    echo ""

    error=1
    for cmd in curl tar docker
    do
        if
            ! command -v "$cmd" >/dev/null
        then
            echo "Error: $cmd is not installed."
            error=0
        fi
    done
    if
        test 0 -eq "$error"
    then
        exit -1
    fi

    # cd to script location
    script_location="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
    cd "$script_location"

    # check if parent directory writable
    if
        ! test -w ..
    then
        echo "\"`readlink -e ..`\" not writeable. Exiting..."
        exit -2
    fi

    if [ -n "$TEST_COOKIE" ]
    then
        download_url=https://github.com/syslifters/sysreptor-ci-test/releases/latest/download/source-prebuilt.tar.gz
    else
        download_url=https://github.com/syslifters/sysreptor/releases/latest/download/source-prebuilt.tar.gz
    fi

    source deploy/.env
    echo "Your current version is $SYSREPTOR_VERSION"

    echo "Checking if update is available..."
    redirect_location=`curl -b "$TEST_COOKIE" -I -s "$download_url" | grep -i ^location | tr -d '\n\r'`
    download=`echo "$redirect_location" | rev | cut -d/ -f 3 | rev`
    version=`echo "$redirect_location" | rev | cut -d/ -f 2 | rev`
    filename=`echo "$redirect_location" | rev | cut -d/ -f 1 | rev`
    if [ "$download" != "download" ] || [ "$filename" != "source-prebuilt.tar.gz" ]
    then
        echo "Checking for new version failed."
        exit -6
    fi
    if [ "$version" == "$SYSREPTOR_VERSION" ]
    then
        echo "The latest SysReptor version is already installed."
        exit 0
    fi
    echo "Found newer version $version"

    echo "Downloading SysReptor from $download_url ..."
    curl -b "$TEST_COOKIE" -s -L --output ../sysreptor.tar.gz "$download_url"

    echo "Checking download..."
    if ! tar -tzf ../sysreptor.tar.gz >/dev/null 2>&1
    then
        echo "Download did not succeed..."
        exit -5
    fi

    echo "Creating backup copy of your current installation..."
    sysreptor_directory=${PWD##*/}
    backup_copy="$sysreptor_directory"-backup-$(date +"%Y-%m-%d-%X")
    cd ..
    mv "$sysreptor_directory" "$backup_copy"
    created_backup=1
    echo "Backup copy located at $backup_copy"

    echo "Unpacking sysreptor.tar.gz..."
    mkdir "$sysreptor_directory"
    tar xzf sysreptor.tar.gz -C "$sysreptor_directory" --strip-components=1

    echo "Copy your app.env..."
    cp "$backup_copy"/deploy/app.env "$sysreptor_directory"/deploy/app.env

    echo "Build and launch SysReptor via docker compose..."
    echo "We are downloading and installing all dependencies."
    echo "This may take a few minutes."
    if grep "^LICENSE=" "$sysreptor_directory"/deploy/app.env
    then
        compose_args=""
    else
        compose_args="-f docker-compose.yml"
    fi
    if
        cd "$sysreptor_directory"/deploy
        ! docker compose $compose_args up -d --build
    then
        echo "Ups. Something did not work while building and launching your containers."
        error_cleanup
    fi

    echo "Nice. Successfully updated."
    echo "Easy peasy lemon squeezy."
