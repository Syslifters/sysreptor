# FAQs for using SysReptor

These FAQs cover the SysReptor application itself: writing reports, designs, API, MFA, and licensing. They apply to self-hosted, Cloud, and SysReptor Labs.

Designer HTML/CSS snippets are in the [report design FAQs](/designer/faqs). Install and ops questions are in [self-hosted](/faq/self-hosted) or [cloud](/faq/cloud). Exam students: [exam report FAQs](/faq/exam-reports).

<FaqExpandAll />

<div class="faq-item">

::: details What is your release cycle?
We aim to release **every two weeks**, usually on **Wednesdays**. Releases include new features, improvements, and bug fixes.

The schedule is not fixed. We ship sooner for urgent bugs or security issues, and later when a change needs more testing. Releases can also land on another weekday.
:::

</div>


<div class="faq-item">

::: details Where can I find the SysReptor changelog?
Find out changelog on [GitHub](https://github.com/syslifters/sysreptor/releases).  
SysReptor installations with outbound connection to the Internet also receive update notifications with links to the latest release and changelog.
:::

</div>


<div class="faq-item" id="vdp">

::: details Do you have a vulnerability disclosure process?
Yes. See the [Syslifters vulnerability disclosure policy](https://handbook.syslifters.com/vulnerability-disclosure).
:::

</div>


<div class="faq-item" id="docx">

::: details Can I export a SysReptor report as DOCX?
No. SysReptor does **not** export Microsoft Word (`.docx`) files.

SysReptor renders pentest reports as **PDF** from the project’s publish page. You can also:

* **Export a project** as a SysReptor `.tar.gz` archive (for backup or import into another instance)
* On **self-hosted** SysReptor, enable the [markdownexport](https://github.com/Syslifters/sysreptor/tree/main/plugins/markdownexport) plugin to export Markdown in a ZIP

:::

</div>


<div class="faq-item">

::: details Where can I find the SysReptor API documentation?
SysReptor’s HTTP API is documented in the [**Swagger UI**](https://demo.sysre.pt/api/public/utils/swagger-ui/) on each instance.

For scripting and automation, we recommend the [`reptor` Python library](/python-library/) or the [`reptor` CLI](/cli/getting-started) instead of calling the HTTP API directly.
:::

</div>


<div class="faq-item">

::: details Why do I have no permissions in the SysReptor report designer?
Editing **global** report designs requires the **Designer** permission. Users without it cannot change shared designs used by others.

Without Designer permission you still have read access to non-private designs. If [private designs](/setup/configuration#private-designs) are enabled, you can create private designs that other users cannot see by default.

To change how **one project's** design, use **Customize Design** on the **Publish** page of that project. This does not require **Designer** permissions.

See [Designs](/designer/designer) and [User permissions](/users/user-permissions#template-editor).
:::

</div>


<div class="faq-item">

::: details I updated the report design but in my project I don't see the changes. Why?
A SysReptor pentest project does **not** keep a live link to the global design you picked at creation time. Creating a project **copies** the design into a project-specific snapshot. Later edits to the original design under **Designs** are not applied automatically to existing projects.

You edited the **global** design, but the project still uses its **snapshot**? To apply the newest global design, go to **Settings** in your project, use the **Design** drop-down to select your global design and save.

If field definitions differ, SysReptor warns that converting might lose data. You can force-change the design or duplicate the project first.
:::

</div>

<div class="faq-item">

::: details Why do I have no permissions in SysReptor finding templates?
Creating and editing **finding templates** requires the **Template Editor** permission. Users without it cannot change templates used by others.

Without Template Editor permission you still have **read access** and can apply templates when writing findings. See [Templates](/finding-templates/overview) and [User permissions](/users/user-permissions#template-editor).
:::

</div>

<div class="faq-item">

::: details Is SysReptor free or paid only?
Large parts of SysReptor are free to use (SysReptor Community). We aim for a free and fully functional reporting tool for freelancers and small teams. We don't add restrictions that prevent commercial usage (such as watermarks, lack of customizations, etc.).

* **SysReptor Community** is free to [self-host](/setup/installation). Some [features and multi-user roles require Professional](https://sysreptor.com/pricing).
* **SysReptor Professional** is [paid](https://sysreptor.com/pricing) (self-hosted license or Cloud).
* **SysReptor Labs** at [labs.sysre.pt](https://labs.sysre.pt) for [HTB](https://htb.sysreptor.com/htb/signup/)/[OffSec](https://offsec.sysreptor.com/offsec/signup/) students is **free** and includes Pro features. See [exam report FAQs](/faq/exam-reports).
:::

</div>


<div class="faq-item" id="mfa">

::: details How do I add 2FA/MFA for a SysReptor user?
On any SysReptor instance, open **your user profile → Security** (`/users/self/security/`) and add a method:

* **Security key (FIDO2 / WebAuthn)**
* **Authenticator app (TOTP)**
* **Backup codes** (store them offline)

You can set a primary method. Superusers or user managers can remove all MFA devices for a user who is locked out (`/users/<user-id>/mfa/`).

On **self-hosted** SysReptor, FIDO2 requires `MFA_FIDO2_RP_ID` set to your hostname. See [Configuration](/setup/configuration#fido2webauthn).

We highly recommend adding MFA for every user account.
:::

</div>


<div class="faq-item">

::: details How do I write re-test reports in SysReptor?
You can write your retest notes directly to your existing project.  
To keep the original report unchanged, **duplicate** the project and add re-test notes in the copy.

We recommend adding the predefined report field **`is_retest`** and finding fields **`retest_status`** and **`retest_notes`** to the design.

1. Add those fields to the design if they are not already there.
2. Set **Is Retest** to true on the project you use for the re-test.
3. Update each finding’s re-test status (Open, Resolved, Partially Resolved, Changed, Accepted, New). Status colors appear in the report sidebar when the design includes `retest_status`.
4. In the PDF design, show retest-only blocks with Vue, for example `v-if="report.is_retest"`. See [Report designer](/designer/designer).
:::

</div>


<div class="faq-item">

::: details How do I export a SysReptor report as PDF?
Open the pentest project’s **publish** page, preview the PDF, then use **Download**. You can set a filename and an optional PDF password.
:::

</div>


<div class="faq-item">

::: details How do I export or import a SysReptor pentest project?
On the **Projects** list, select one or more projects and export a `.tar.gz` archive (with or without notes). Import uses the import button on the same list.

Project export does **not** include the [version history](/reporting/version-history) and [comments](/reporting/comments-and-review#comments).
:::

</div>


::: info <DocBadge icon="mdi:help-circle" class="lg middle" label="Further questions?" />
Need help or have questions? Get support and [connect with us and the SysReptor community](https://github.com/Syslifters/sysreptor/discussions/).
:::
