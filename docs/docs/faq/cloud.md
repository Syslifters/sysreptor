# FAQs for SysReptor Cloud

These FAQs are for **SysReptor Cloud** (hosted by Syslifters for organizations).

If you write **HTB, OffSec, or other exam reports** on [labs.sysre.pt](https://labs.sysre.pt), use the [exam report FAQs](/faq/exam-reports) instead. Self-hosted Docker installs are covered in the [self-hosted FAQs](/faq/self-hosted).

<FaqExpandAll />

<div class="faq-item">

::: details What is SysReptor Cloud compared to self-hosted SysReptor and labs.sysre.pt?
There are three common ways to use SysReptor:

* **Self-hosted:** you install SysReptor with Docker on your own server. Self-hosted can be SysReptor Community (free) or SysReptor Professional (paid). See [Installation](/setup/installation), [pricing](https://sysreptor.com/pricing) and [self-hosted FAQs](/faq/self-hosted).
* **SysReptor Cloud:** Syslifters hosts SysReptor Professional for your organization (paid). See [pricing](https://sysreptor.com/pricing).
* **SysReptor Labs:** the free exam-reporting service at [labs.sysre.pt](https://labs.sysre.pt) hosted in the SysReptor Cloud for students writing certification and exam reports. See the [exam report FAQs](/faq/exam-reports).

The [public playground](https://sysreptor.com/demo) is a demo installation hosted in the SysReptor Cloud.
:::

</div>


<div class="faq-item">

::: details Is SysReptor Cloud free?
SysReptor Cloud is a paid hosted offering. See [pricing](https://sysreptor.com/pricing).

**SysReptor Labs** at [labs.sysre.pt](https://labs.sysre.pt) for HTB/OffSec students is free; that is a non-commercial service.
:::

</div>


<div class="faq-item" id="hosted">

::: details Where is SysReptor Cloud hosted?
SysReptor Cloud currently runs in **Germany** on physical servers at [Hetzner Online GmbH](https://www.hetzner.com/). We operate a self-managed Kubernetes cluster there on physical servers.  
We guarantee that if new sites are added in the future, their location will be within the European Union (EU).
:::

</div>


<div class="faq-item" id="privacy-laws">

::: details What data privacy laws apply?
Personal data in Cloud is processed under the **GDPR**. The Cloud contract is governed by Austrian law.
:::

</div>


<div class="faq-item" id="dpa">

::: details Can I have a signed DPA (AVV)?
Yes. Please [contact us](/contact-us#contact-information).
:::

</div>


<div class="faq-item" id="eu-data">

::: details Does any Cloud customer data leave the EU/EEA?
No.
:::

</div>


<div class="faq-item" id="encryption">

::: details Is data encrypted in transit and at rest?
Yes. Data in transit is encrypted with **HTTPS**. At rest, all data is stored on an encrypted **ZFS** partition. In addition, every Cloud installation has its own encryption key for database and file/asset encryption. See [Data Encryption at Rest](/setup/configuration#data-encryption-at-rest).
:::

</div>


<div class="faq-item" id="tenant-isolation">

::: details Are Cloud tenants isolated from each other?
Yes. Each customer runs in a dedicated Kubernetes namespace with network separation. Each installation uses its own encryption keys.

PDF rendering pods are shared, but each pod is disposed after one use so rendering jobs cannot interfere with another customer. See [Architecture](/insights/architecture).
:::

</div>


<div class="faq-item" id="third-parties">

::: details Does SysReptor send report contents to third parties, e.g., for spell check or AI?
No. Spell check runs inside your Cloud installation ([LanguageTool](/reporting/spell-check)). Report content is sent to an LLM only if you [configure an AI provider](/reporting/ai-agent) in settings.
:::

</div>


<div class="faq-item" id="ai-training">

::: details Do you use my reports to train AI models?
No.
:::

</div>


<div class="faq-item" id="custom-domain">

::: details Can I use my own domain name for hosting?
Yes. Please [contact us](/contact-us#contact-information).
:::

</div>


<div class="faq-item" id="sso">

::: details Can I require SSO (OIDC) and disable password login?
Yes. Superusers can enable [OIDC SSO](/users/oidc-setup) and disable username/password login in **Settings → Authentication Settings** (`LOCAL_USER_AUTH_ENABLED=false`). See [SSO configuration](/setup/configuration#single-sign-on-sso).  
You can disable local user authentication for the entire installation, or on a per-user basis.
:::

</div>


<div class="faq-item">

::: details Can I install plugins on SysReptor Cloud?
Yes. [Official plugins](/setup/plugins#official-plugins) that ship with SysReptor can be enabled in settings.

**Custom plugins** are only supported in self-hosted SysReptor, not in the cloud version.
:::

</div>


<div class="faq-item" id="reptor-cli">

::: details Can Cloud users use the reptor CLI?
Yes. Create an API token in your user profile and configure `reptor` with your Cloud URL. See the [`reptor` CLI documentation](/cli/getting-started).
:::

</div>


<div class="faq-item">

::: details How do I reset my password on SysReptor Cloud?
Administrators with superuser or user manager permissions can reset user passwords in the Users UI. See the [full steps](/users/forgot-password#reset-password-via-user-admin-interface).

If your cloud installation has the **Forgot Password** functionality enabled, you can use it to receive an email for setting a new password. You will still need your second authentication factor, if configured for your user account to successfully authenticate.

Students on SysReptor Labs can [reset their password](https://labs.sysre.pt/login/forgot-password/) online.
:::

</div>


<div class="faq-item">

::: details Can I create backups of a SysReptor Cloud instance?
Yes. You can [create a backup via web interface](/setup/backups#create-backups-via-web-interface) with your SysReptor installation's [`BACKUP_KEY`](/setup/configuration#backup-key) and you must have **superuser** permissions. 
Please [contact us](/contact-us#contact-information) to receive your `BACKUP_KEY`.

You can always **export individual projects** as `.tar.gz` from the projects list. This is not a full instance backup.
:::

</div>


<div class="faq-item" id="backups-location">

::: details Where are backups stored?
On our own servers in Austria. Each backup is encrypted with a dedicated symmetric key. That key is encrypted with an asymmetric key. Private keys for recovering the symmetric encryption keys are stored on hardware tokens with PIN protection.
:::

</div>


<div class="faq-item" id="backup-retention">

::: details How long are backups stored?

* **Daily backups:** 21 days
* **Weekly backups:** 35 days
* **Monthly backups:** 365 days
:::

</div>


<div class="faq-item" id="delete-instance">

::: details Can you delete my instance and confirm it?
Yes. Please [contact us](/contact-us#contact-information). We can delete your Cloud instance and confirm the deletion.
:::

</div>


<div class="faq-item">

::: details Can I migrate from SysReptor Cloud to a self-hosted SysReptor?
Yes, you can [create a backup](/setup/backups#create-backups-via-web-interface) and restore it on a self-hosted SysReptor installation.

You can also move project data by **exporting projects** from Cloud (projects list → export `.tar.gz`) and **importing** them on a [self-hosted](/setup/installation) instance.

:::

</div>


<div class="faq-item">

::: details Can I migrate from a self-hosted SysReptor to SysReptor Cloud?
Yes, you can [create a backup](/setup/backups) and [contact us](/contact-us#contact-information) to restore it on a SysReptor Cloud installation.

You can also move project data by **exporting projects** from self-hosted (projects list → export `.tar.gz`) and **importing** them on Cloud.

:::

</div>


<div class="faq-item" id="availability">

::: details Is there a track record for SysReptor Cloud's availability?
Yes. See the [SysReptor Cloud status page](https://status.sysreptor.com/).
:::

</div>


<div class="faq-item" id="maintenance">

::: details What is the maintenance window?
Wednesdays and Saturdays, 08:00–11:00 GMT.

Planned maintenance is also announced on the [SysReptor Cloud status page](https://status.sysreptor.com/). You can subscribe there for updates.
:::

</div>


::: info <DocBadge icon="mdi:help-circle" class="lg middle" label="Further questions?" />
Need help or have questions? Get support and [connect with us and the SysReptor community](https://github.com/Syslifters/sysreptor/discussions/).
:::
