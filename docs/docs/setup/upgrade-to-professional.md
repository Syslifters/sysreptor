# Upgrade to Professional

<BadgeSelfHosted />

You can upgrade from SysReptor Community to SysReptor Professional anytime without reinstallation. All your data will be preserved.  
Here's how:

1. Add your license key to `deploy/app.env` (`LICENSE='your_license_key'`)
2. Add languagetool to `deploy/docker-compose.yml`:
   ```
   name: sysreptor

   include:
     - sysreptor/docker-compose.yml
     - languagetool/docker-compose.yml
   ```
3. `cd` to `deploy` and run `docker compose up -d`
4. Enjoy

## From Professional to Community

For reverting to community, remove or comment out the license key from `deploy/app.env`.  
You can also remove `languagetool/docker-compose.yml` from `deploy/docker-compose.yml`. This saves resources (one docker container), as languagetool is not available in SysReptor Community.

Moving from Professional to Community does not result in data loss. All data will be preserved.  
Non-superuser accounts, will, however, no longer be able to log in.

::: info <DocBadge icon="mdi:calendar" label="Book a demo" />

Interested in SysReptor Professional?  
Book a Teams call with us and get you questions answered.

[Choose your time slot](https://cloud.syslifters.com/apps/appointments/pub/tBtAMcEwczA5CDMv/form)

:::
