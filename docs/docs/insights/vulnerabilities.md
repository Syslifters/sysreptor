## Cross-Site Websocket Hijacking in SysReptor (CVE-2024-36076)

**CVSSv3.1:** Medium (6.8; CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:H/I:H/A:N)  
**Affected versions** 2024.28 to 2024.30  
**Fixed in 2024.40** (on 25 May 2024)  

Cross-Site WebSocket Hijacking in SysReptor from version 2024.28 to version 2024.30 causes attackers to gain read and write access to personal notes and project notes when a logged-in SysReptor user visits a malicious same-site subdomain in the same browser session.

Credits go to our colleague [Christoph Mahrl](https://docs.syslifters.com/en/christoph/){ target=_blank }.  
Find more information in our [advisory](https://github.com/Syslifters/sysreptor/security/advisories/GHSA-2vfc-3h43-vghh){ target=_blank }.


## HTTP Request Smuggling in non-recommended configurations (CVE-2024-1135)

**CVSSv3.1:** High (7.8; CVSS:3.1/AV:L/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H)  
**Fixed in 2024.29** (on 17 April 2024)  
**Workaround:** Use a reverse proxy (like [Caddy](../setup/webserver.md#caddy) or [nginx](../setup/webserver.md#nginx)).

If you don't use a reverse proxy (like Caddy or nginx) for SysReptor and expose the SysReptor port (TCP 8000 by default) directly, you are probably vulnerable to HTTP Request Smuggling attacks.

This is due to an unpatched [vulnerability in gunicorn](https://huntr.com/bounties/22158e34-cfd5-41ad-97e0-a780773d96c1){ target=_blank }. The vulnerability could be well-exploitable for authenticated users and might lead to privilege escalation.

