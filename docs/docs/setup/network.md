# Network Settings
:octicons-server-24: Self-Hosted

## Bind to different port or interface
SysReptor is bound to port 8000 on localhost by default. If you want to bind it to a different port, use the `BIND_PORT` environment variable and restart your containers from the `deploy` directory.  

The format is `IP:HOST_PORT:CONTAINER_PORT`(note that `CONTAINER_PORT` should always be 8000).

``` title="Examples:"
export BIND_PORT="127.0.0.1:8000:8000"
export BIND_PORT="127.0.0.1:80:8000"  # Bind to localhost port 80
export BIND_PORT="8000:8000"  # Bind to all interfaces
export BIND_PORT="1.1.1.1:8000:8000"  # Bind to dedicated interface
```

```bash linenums="1" title="Export port variable and run container"
export BIND_PORT="127.0.0.1:8000:8000"
cd deploy
docker compose up -d
```

Binding SysReptor to a publicly reachable network port exposes the application to untrusted networks without encryption. We recommend setting up a [web server](webserver/).

Make sure that environment variables are set persistently, e.g. by adding the `export` command to your `~/.profile`.

## Proxy Configuration

We pass the proxy environment variables (`HTTP_PROXY` and `HTTPS_PROXY`) from your host system into the Docker containers. To use a proxy, set those variables on your host system and start your containers from the `deploy` directory.

```bash title="Export proxy variables and run container"
export HTTP_PROXY="http://192.168.0.111:8080"
export HTTPS_PROXY="http://192.168.0.111:8080"
cd deploy
docker compose up -d
```

!!! info "The proxy server must be reachable from container"

    Make sure that the proxy server is reachable from inside your docker container.
    Loopback addresses (e. g. `127.0.0.1`) or `localhost` will not work.

Make sure that environment variables are set persistently, e.g. by adding the `export` command to your `~/.profile`.

### CA Certificates

Your proxy server will probably not have a publicly trusted CA certificate. Build your Docker image with custom CA certificates:

```bash title="Set CA certificate, build and run"
cd deploy
export SYSREPTOR_CA_CERTIFICATES="-----BEGIN CERTIFICATE-----\nMIIDqDCCApCgAwIBAgIFAMjv7sswDQYJKoZIhv..."
docker compose up -d --build
```

Make sure that environment variables are set persistently, e.g. by adding the `export` command to your `~/.profile`.