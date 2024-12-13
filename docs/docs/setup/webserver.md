# Setup Webserver

:octicons-server-24: Self-Hosted

The Django webserver is not recommended due to missing transport encryption, missing performance and security tests.  
We recommend a webserver like Caddy, [nginx](webserver-nginx.md) or Apache and to enable https.

## Easy setup with Caddy (recommended) {#caddy}

You can run `setup.sh` in `deploy/caddy` to set up an additional Docker container with Caddy as a webserver.  

```
bash deploy/caddy/setup.sh
```

### Optional: LetsEncrypt HTTPS certificate
If you want Caddy to take care of your LetsEncrypt certificate, you must set up:

 1. a valid domain name resolving to your public IP address
 2. port 80 of your must be publicly reachable

