# Setup Webserver

:octicons-server-24: Self-Hosted

The Django webserver is not recommended due to missing transport encryption, missing performance and security tests.  
We recommend a webserver like Caddy, nginx or Apache and to enable https.

## Easy setup with Caddy (recommended)

You can run `setup.sh` in `deploy/caddy` to set up an additional Docker container with Caddy as a webserver.  

```
bash deploy/caddy/setup.sh
```

### Optional: LetsEncrypt HTTPS certificate
If you want Caddy to take care of your LetsEncrypt certificate, you must set up:

 1. a valid domain name resolving to your public IP address
 2. port 80 of your must be publicly reachable

## nginx

Install nginx on your host system:

```shell
sudo apt-get update
sudo apt-get install -y nginx
```

Copy our nginx boilerplate configuration from the `deploy/nginx` directory to your nginx directory:

```shell
sudo cp deploy/nginx/sysreptor.nginx /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/sysreptor.nginx /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
```

You can optionally generate self-signed certificates:
```shell
sudo apt-get update
sudo apt-get install -y ssl-cert
sudo make-ssl-cert generate-default-snakeoil
```

Modify `sysreptor.nginx` and update the certificate paths in case you have trusted certificates (recommended).

(Re)Start nginx:
```shell
sudo systemctl restart nginx
# sudo /etc/init.d/nginx restart
```
