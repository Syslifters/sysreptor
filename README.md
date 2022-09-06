# SysReptor
## Getting started
### Prerequisites
* Ubuntu
* 8GB RAM for building the image (or 4GB + 8GB swap)
* 4GB RAM for operating the server
* Latest [Docker](https://docs.docker.com/engine/install/){ target=_blank }
* Latest [Docker Compose](https://docs.docker.com/compose/install/){ target=_blank }
* Latest Chrome, Edge, Firefox (Safari currently not officially supported)

### Quick Install
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

## Documentation
Find further documentation (how to add users, etc) at [https://docs.sysreptor.com](https://docs.sysreptor.com)