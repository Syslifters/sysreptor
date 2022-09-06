# SysReptor Docs
We are currently in a Proof-of-Concept phase for our pentesting reporting software SysReptor.

Selected PoC customers got access to our currently private repository.

We plan to release the core features free to use for pentesting companies.  
There will also be a commercial edition with additional features.

# Getting started
## Prerequisites
* Ubuntu
* 8GB RAM for building the image (or 4GB + 8GB swap)
* 4GB RAM for operating the server
* Latest [Docker](https://docs.docker.com/engine/install/){ target=_blank }
* Latest [Docker Compose](https://docs.docker.com/compose/install/){ target=_blank }
* Latest Chrome, Edge, Firefox (Safari currently not officially supported)

## Install
```shell linenums="1"
git clone https://github.com/Syslifters/sysreptor.git
# Alternative via SSH: git clone git@github.com:Syslifters/sysreptor.git
cd deploy
cp app.env.example app.env
# Update keys and credentials in app.env (e.g. SECRET_KEY) 
# Optionally update database credentials in docker-compose.yml
docker compose up --build -d
# This command might take a few minutes when you run it the first time
# It is building your image and preparing all the nice stuff you will want to use
docker compose exec app python3 manage.py createsuperuser
# Now you have to specify your initial user's name and password
```
You can now access your application with your favourite browser at http://localhost:8000/.

## Recommended: Setup nginx Server
It is not recommended to use the Django webserver due to missing transport encryption, missing security tests and performance tests.  
We recommend to user a webserver like nginx or Apache and enable to https.

You can install nginx on your host system. E.g. on Debian-based systems with apt-get:

```shell linenums="1"
sudo apt-get update
sudo apt-get install nginx
```

Copy our nginx boilerplate configuration from the `deploy` directory to your nginx directory, e.g.:

```shell linenums="1"
sudo cp deploy/sysreptor.nginx /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/sysreptor.nginx /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
```

You can optionally generate self-signed certificates:
```shell linenums="1"
sudo apt-get update
sudo apt-get install ssl-cert
sudo make-ssl-cert generate-default-snakeoil
```

Modify `sysreptor.nginx` and update the certificate paths in case you have trusted certificates (recommended).

(Re)Start nginx:
```shell linenums="1"
sudo systemctl restart nginx
# sudo /etc/init.d/nginx restart
```

## Add New Users
Adding new users is possible via the Django backend only.
Go to https://<sysreptor\>/admin/users/pentestuser/add/ and specify username and password.
Click "Save and continue editing" to manage permissions and additional attributes.

![Add user via Django backend](/images/add-user.png)

See [User Permissions](/user-permissions) for details.

## How to Update
```shell linenums="1"
git pull
cd deploy
docker compose up --build -d
```

## License
We currently offer our software under the [PolyForm Internal Use License 1.0.0](/license).
