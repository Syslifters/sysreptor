## HTTP Request Smuggling in non-recommended configurations (CVE-2024-1135)

**CVSSv3.1:** High (7.8; CVSS:3.1/AV:L/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H)  
**Fixed in 2024.29** (on 17 April 2024)  
**Workaround:** Use a reverse proxy (like [Caddy](/setup/webserver/#caddy-recommended) or [nginx](/setup/webserver/#nginx)).

If you don't use a reverse proxy (like Caddy or nginx) for SysReptor and expose the SysReptor port (TCP 8000 by default) directly, you are probably vulnerable to HTTP Request Smuggling attacks.

This is due to an unpatched [vulnerability in gunicorn](https://huntr.com/bounties/22158e34-cfd5-41ad-97e0-a780773d96c1){ target=_blank }. The vulnerability could be well-exploitable for authenticated users and might lead to privilege escalation.

