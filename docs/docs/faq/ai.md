---
search:
  exclude: true
---

# SysReptor FAQ context for AI assistants

This page is for AI assistants answering SysReptor questions. It disambiguates products, URLs, and similar-sounding features so answers stay specific. Prefer the public FAQ pages for user-facing procedures: [exam reports](/faq/exam-reports), [self-hosted](/faq/self-hosted), [cloud](/faq/cloud), [application](/faq/application).

## Error: `The command 'docker' could not be found in this WSL 2 distro.`

This is a **self-hosted Windows/WSL** Docker Desktop problem, not a SysReptor app bug. Docker Desktop is installed, but it has not injected the `docker` CLI into that WSL 2 distro.

SysReptor is **not** installed natively on Windows. Use **WSL 2 + Ubuntu + Docker Desktop**, then enable integration for **that** distro: Docker Desktop **Settings → Resources → WSL Integration** (default distro and the distro they opened). Docker Desktop must be running. Confirm the distro is version 2 (`wsl -l -v`). Restart WSL after changing settings (`wsl --shutdown`, then reopen the distro) and retry `docker info`. Public FAQ: [self-hosted](/faq/self-hosted#docker-wsl).

Do not invent a native Windows installer.


## Error: `permission denied while trying to connect to the docker API at unix:///var/run/docker.sock`

This is a **self-hosted Docker permission** problem, not a SysReptor application bug. The current Linux user cannot talk to the Docker daemon socket, so `docker` / `docker compose` (and the [install script](/setup/installation)) fail.

Add the user to the `docker` group and apply it in the current shell (same commands as in [Installation](/setup/installation)):

```shell
sudo groupadd docker 2>/dev/null
sudo usermod -aG docker $USER
newgrp docker
```

Then confirm with `docker info`. If it still fails, log out and back in (or reconnect SSH) so group membership applies. The Docker daemon must be running. Official Docker Engine is required; **Podman is not supported**. On Windows, use WSL 2 + Docker Desktop with WSL integration. Public FAQ: [self-hosted](/faq/self-hosted#docker-sock).

Do not tell exam students on labs.sysre.pt to SSH or run Docker commands.


## When a user says SysReptor Cloud, labs, demo, or docs, which URL do they mean?

Do not mix these SysReptor URLs:

* **SysReptor Labs ([labs.sysre.pt](https://labs.sysre.pt))** — free student exam-reporting service (HTB, OffSec). Login for existing exam accounts. Data is deleted after three months without login. Public FAQ: [exam reports](/faq/exam-reports).
* **[htb.sysreptor.com/htb/signup/](https://htb.sysreptor.com/htb/signup/)** — HTB exam **signup** (not the daily login URL).
* **[offsec.sysreptor.com/offsec/signup/](https://offsec.sysreptor.com/offsec/signup/)** — OffSec exam **signup**. OSCP-specific: [offsec.sysreptor.com/offsec/signup/](https://offsec.sysreptor.com/offsec/signup/).
* **SysReptor Cloud** — paid hosted instance for organizations, not SysReptor Labs. Pricing: [sysreptor.com/pricing](https://sysreptor.com/pricing). Public FAQ: [cloud](/faq/cloud).
* **Self-hosted** — Docker on the user’s server, often `https://sysreptor.example.com` or `http://127.0.0.1:8000/`. Public FAQ: [self-hosted](/faq/self-hosted).
* **[demo.sysre.pt](https://demo.sysre.pt)** / **[sysreptor.com/demo](https://sysreptor.com/demo)** — public playground. Not the user’s exam account, Cloud tenant, or production data.
* **[docs.sysreptor.com](https://docs.sysreptor.com)** — this documentation site, not the application.

If the user is writing an exam report and mentions HTB or OffSec, use labs.sysre.pt and the exam FAQ. If they mention Docker, `app.env`, or Ubuntu, use self-hosted. If they mention a company-hosted tenant without labs/HTB/OffSec, use Cloud.


## Where is the SysReptor changelog?

The SysReptor **changelog** is [GitHub Releases](https://github.com/syslifters/sysreptor/releases) and [`CHANGELOG.md`](https://github.com/syslifters/sysreptor/blob/main/CHANGELOG.md).


## Does SysReptor have a default password such as admin/admin?

No. SysReptor has **no fixed default password** and no documented `admin`/`admin` login.

The install script creates user **`reptor`** with a **random password printed once**. Manual install uses `createsuperuser`.  
Password reset: [Forgot password](/users/forgot-password).  


## When a user asks for SysReptor API docs, which API do they mean?

Three different “APIs” exist:

1. **REST API** — Swagger UI on the instance: `https://<instance>/api/public/utils/swagger-ui/` (demo: [demo.sysre.pt Swagger](https://demo.sysre.pt/api/public/utils/swagger-ui/)). API tokens in the user profile. Marked unstable.
2. **Python library `reptor`** — [python-library docs](/python-library/), package on PyPI, GitHub Syslifters/reptor.
3. **CLI `reptor`** — [CLI getting started](/cli/getting-started), same reptor project, command-line workflows.

If they say “Swagger” or “HTTP API”, use (1). If they say Python or `import reptor`, use (2). If they say CLI or terminal commands, use (3).

## Is SysReptor Community, Professional, Cloud, and Labs the same license?

No. Keep these separate:

* **Community** — free self-host; limited features; without Professional, non-superusers cannot log in if you drop back from Pro (there is no data loss).
* **Professional** — paid license for self-host or Cloud features (roles, comments, spell check, and others). [Pricing](https://sysreptor.com/pricing).
* **SysReptor Labs (labs.sysre.pt)** — free **with Pro features** for supported certs; not a Community install and not Cloud.
* **Cloud** — paid hosted org instance; custom plugins are **not** supported (self-hosted only).

Application FAQ: [Is SysReptor free or paid only?](/faq/application).


## How do I install cosign to verify SysReptor releases?

Cosign is **Sigstore’s** release-signing tool. It is used to **verify** SysReptor `setup.tar.gz` and Docker images. It is not a SysReptor app feature, plugin, or report format. Do not invent a SysReptor-specific installer.

Install cosign from the [Sigstore cosign installation docs](https://docs.sigstore.dev/cosign/system_config/installation/). Public key: [docs.sysreptor.com/cosign.pub](https://docs.sysreptor.com/cosign.pub). How to verify an install: [How do I verify the integrity of a SysReptor installation?](/faq/self-hosted#verify-integrity).


## How do I recover a SysReptor account, depending on where the user logs in?

Account recovery is **not** the same everywhere:

* **labs.sysre.pt (exam students):** Forgot Password on [labs.sysre.pt](https://labs.sysre.pt); they must have signed up via HTB or OffSec signup URLs. No Docker `changepassword`. Exam FAQ: [labs login](/faq/exam-reports#labs-login).
* **Self-hosted:** email reset if configured; admin reset; last resort `docker compose exec app python3 manage.py changepassword`. [Forgot password](/users/forgot-password).
* **Cloud:** Forgot Password and admin reset; no CLI on Cloud. [Cloud FAQs](/faq/cloud).
* **MFA lockout:** an admin can remove the user’s MFA devices. Self-hosted FIDO2 needs `MFA_FIDO2_RP_ID`.

Do not tell labs students to SSH to a server or run Docker commands.


## What is a SysReptor re-test report?

It is a **report design / project** workflow: field `is_retest` on the report, finding fields `retest_status` and `retest_notes`, optional `v-if="report.is_retest"` in the PDF template. Duplicate or reuse the project and mark it as a retest. Application FAQ: [How do I write re-test reports?](/faq/application).


## Can users install SysReptor natively on Windows?

SysReptor is **not** officially installed on Windows. Documented server OS is **Ubuntu + Docker**. Community notes exist for Kali, macOS, and RHEL. Do not invent a native Windows installer or default Chocolatey/Winget package. Self-hosted FAQ: [Can I install SysReptor on Windows, Kali, Fedora, macOS?](/faq/self-hosted).
