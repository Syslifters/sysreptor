# Upgrade to PRO

:octicons-server-24: Self-Hosted

1. Add your license key to `deploy/app.env` (`LICENSE='your_license_key'`)
2. Add `languagetool/docker-compose.yml` to `docker-compose.yml` in the `deploy` directory:
   ```
   name: sysreptor

   include:
     - sysreptor/docker-compose.yml
     - languagetool/docker-compose.yml
   ```
3. `cd` to `deploy` and run `docker compose up -d`
4. Enjoy
