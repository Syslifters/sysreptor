# Proxy Server
:octicons-server-24: Self-Hosted

Your SysReptor server should use a proxy for outbound connections? Here's how to configure.

## Proxy Configuration

We pass the proxy environment variables (`HTTP_PROXY` and `HTTPS_PROXY`) from your host system into the Docker containers. To use a proxy, set those variables on your host system and start your containers from the `deploy` directory.

=== "Professional"
    ```bash linenums="1" title="Export proxy variables and run container"
    export HTTP_PROXY="http://192.168.0.111:8080"
    export HTTPS_PROXY="http://192.168.0.111:8080"
    cd deploy
    docker compose up -d
    ```
=== "Community"
    ```bash linenums="1" title="Export proxy variables and run container"
    export HTTP_PROXY="http://192.168.0.111:8080"
    export HTTPS_PROXY="http://192.168.0.111:8080"
    cd deploy
    docker compose -f docker-compose.yml up -d
    ```

!!! info "The proxy server must be reachable from container"

    Make sure that the proxy server is reachable from inside your docker container.
    Loopback addresses (e. g. `127.0.0.1`) or `localhost` will not work.


## CA Certificates

Your proxy server will probably not have a publicly trusted CA certificate. Build your Docker image with custom CA certificates:

=== "Professional"
    ```bash linenums="1" title="Set CA certificate, build and run"
    cd deploy
    export SYSREPTOR_CA_CERTIFICATES="-----BEGIN CERTIFICATE-----\nMIIDqDCCApCgAwIBAgIFAMjv7sswDQYJKoZIhv..."
    docker compose up -d --build
    ```
=== "Community"
    ```bash linenums="1" title="Set CA certificate, build and run"
    cd deploy
    export SYSREPTOR_CA_CERTIFICATES="-----BEGIN CERTIFICATE-----\nMIIDqDCCApCgAwIBAgIFAMjv7sswDQYJKoZIhv..."
    docker compose -f docker-compose.yml up -d --build
    ```

Make sure that the `SYSREPTOR_CA_CERTIFICATES` environment variable is set during [updates](../updates) to keep your custom CA trusted.