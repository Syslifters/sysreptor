# Installation
## Prerequisites
### Server
:octicons-server-24: Self-Hosted

* Ubuntu
* 8GB RAM (or 4GB + 8GB swap)
* Latest [Docker](https://docs.docker.com/engine/install/){ target=_blank }
* Latest [Docker Compose](https://docs.docker.com/compose/install/){ target=_blank }

### Client
:octicons-cloud-24: Cloud · :octicons-server-24: Self-Hosted

* Network connection to the server
* Up-to-date browser, one of:
    * Chrome
    * Edge
    * Firefox
    * Safari

## Install
:octicons-server-24: Self-Hosted

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
:octicons-server-24: Self-Hosted

It is not recommended to use the Django webserver due to missing transport encryption, missing performance and security tests.  
We recommend to user a webserver like nginx or Apache and to enable https.

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

## Update
:octicons-server-24: Self-Hosted

```shell linenums="1"
git pull
cd deploy
docker compose up --build -d
```

## License
:octicons-server-24: Self-Hosted

We offer our software under our [SysReptor License](/license).
