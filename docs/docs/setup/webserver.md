# Setup Webserver

:octicons-server-24: Self-Hosted

The Django webserver is not recommended due to missing transport encryption, missing performance and security tests.  
We recommend a webserver like Caddy, nginx or Apache and to enable https.

=== "Caddy (recommended)"
    [Caddy](https://caddyserver.com/){ target=_blank } is an open-source webserver with automatic HTTPS written in Go.

    Setup your DNS A-record pointing to your server. Make sure that ports 443 and 80 are publicly available. (You need port 80 for getting your LetEncrypt certificate.)

    Create a `docker-compose.yml` (e.g. in a `caddy` directory outside your SysReptor files):

    ```yml
    version: '3.9'
    name: caddy

    services:
      caddy:
        image: caddy:latest
        container_name: 'sysreptor-caddy'
        restart: unless-stopped
        command: caddy reverse-proxy --from https://<your-domain>:443 --to http://127.0.0.1:8000
        volumes:
        - type: volume
          source: sysreptor-caddy-data
          target: /data
        network_mode: "host"

    volumes:
      sysreptor-caddy-data:
        name: sysreptor-caddy-data
    ```

    Don't forget to replace `<your-domain>` by your domain.
    
    `docker compose up -d` and enjoy.

=== "nginx"

    You can install nginx on your host system:

    ```shell
    sudo apt-get update
    sudo apt-get install nginx
    ```

    Copy our nginx boilerplate configuration from the `deploy` directory to your nginx directory:

    ```shell
    sudo cp deploy/sysreptor.nginx /etc/nginx/sites-available/
    sudo ln -s /etc/nginx/sites-available/sysreptor.nginx /etc/nginx/sites-enabled/
    sudo rm /etc/nginx/sites-enabled/default
    ```

    You can optionally generate self-signed certificates:
    ```shell
    sudo apt-get update
    sudo apt-get install ssl-cert
    sudo make-ssl-cert generate-default-snakeoil
    ```

    Modify `sysreptor.nginx` and update the certificate paths in case you have trusted certificates (recommended).

    (Re)Start nginx:
    ```shell
    sudo systemctl restart nginx
    # sudo /etc/init.d/nginx restart
    ```
