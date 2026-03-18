# Upgrade to PRO

:octicons-server-24: Self-Hosted

You can upgrade from SysReptor Community to SysReptor Professional anytime without reinstallation. All your data will be preserved.  
Here's how:

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


<div class="grid cards" style="margin-top: 2em;" markdown>

-   :material-calendar:{ .lg .middle } __Book a demo__

    ---

    Interested in SysReptor Professional?  
    Book a Teams call with us and get you questions answered.

    [:octicons-arrow-right-24: Choose your time slot](https://cloud.syslifters.com/apps/appointments/pub/tBtAMcEwczA5CDMv/form
){ target="_blank"}

</div>
