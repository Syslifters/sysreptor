# Use nginx as a web server

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
