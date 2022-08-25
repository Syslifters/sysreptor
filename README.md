# SysReptor
## Getting started
### Prerequisites
* Ubuntu
* Latest [Docker](https://docs.docker.com/engine/install/){ target=_blank }
* Latest [Docker Compose](https://docs.docker.com/compose/install/){ target=_blank }
* Latest Chrome, Edge, Firefox (Safari currently not officially supported)

### Quick Install
```shell linenums="1"
git clone https://github.com/Syslifters/sysreptor.git
# Alternative via SSH: git clone git@github.com:Syslifters/sysreptor.git
cd deploy
docker compose build app
# This command might take a few minutes when you run it the first time
# It is building your image and preparing all the nice stuff you will want to use
docker compose run app python3 manage.py createsuperuser
# Now you have to specify your initial user's name and password
docker compose up -d
```
You can now access your application with your favourite browser at http://localhost:8000/.

## Documentation
Find further documentation (how to add users, etc) at [https://docs.sysreptor.com](https://docs.sysreptor.com)