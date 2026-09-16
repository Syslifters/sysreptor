# FAQs for students writing exam reports

These FAQs are for students who write Hack The Box, OffSec, and other certification exam reports in the free SysReptor Labs at [labs.sysre.pt](https://labs.sysre.pt).

If you run SysReptor on your own server, see the [self-hosted FAQs](/faq/self-hosted). For SysReptor Cloud, see the [cloud FAQs](/faq/cloud).

<FaqExpandAll />

<div class="faq-item">

::: details What is SysReptor Labs at labs.sysre.pt?
[labs.sysre.pt](https://labs.sysre.pt) is SysReptor’s free cloud for writing certification exam reports. You write the report in Markdown and render it as PDF. It includes pro features and no self-hosted setup is required.

It is not the same as [SysReptor Cloud](/faq/cloud) or a [self-hosted](/faq/self-hosted) SysReptor instance. 
Even though the functionality largely corresponds to SysReptor Professional, some functionalities are limited: You don't receive superuser permissions, collaboration with other users is restricted, you cannot edit global designs.
:::

</div>


<div class="faq-item">

::: details Where do I register for HTB, OffSec, or other certification reporting in SysReptor?
Register for the free SysReptor Labs with the signup page for your certification provider:

* Hack The Box: [htb.sysreptor.com/htb/signup/](https://htb.sysreptor.com/htb/signup/)
* OffSec (including OSCP+): [offsec.sysreptor.com/offsec/signup/](https://offsec.sysreptor.com/offsec/signup/)

For other certifications or projects, sign up at any of the two links. You can create or import SysReptor designs as private designs in your user account.

Depending on the registration link, your user will receive HTB or Offsec demo reports imported by default. The platform and user capabilities are the same for both links.

After signup, log in at [labs.sysre.pt](https://labs.sysre.pt).
:::

</div>


<div class="faq-item">

::: details Where do I log in to write HTB or OffSec exam reports in SysReptor?
Log in to SysReptor Labs at [labs.sysre.pt](https://labs.sysre.pt).

Signup is separate from login:

* HTB signup: [htb.sysreptor.com/htb/signup/](https://htb.sysreptor.com/htb/signup/)
* OffSec signup: [offsec.sysreptor.com/offsec/signup/](https://offsec.sysreptor.com/offsec/signup/)
:::

</div>


<div class="faq-item">

::: details Which certifications does the free SysReptor Labs support?
We currently provide the following report designs:

* **Hack The Box:** CPTS, CWES, CDSA, CWEE, CAPE, CJCA, CWPE, COAE
* **OffSec:** OSCP+, OSEP, OSWP, OSWA, OSWE, OSED, OSMR, OSEE, OSDA, OSIR, OSTH, OSAI

Demo PDFs and designs are listed on [HTB reporting](/htb-reporting-with-sysreptor), [OffSec reporting](/offsec-reporting-with-sysreptor), and [demo reports](/demo-reports).

You can import any other design as private design.
:::

</div>


<div class="faq-item">

::: details Is SysReptor Labs free?
Yes. SysReptor Labs at [labs.sysre.pt](https://labs.sysre.pt) is free for writing certification exam reports. It includes Pro features and does not require a SysReptor Professional license.  
There is no limit in the number of reports or projects you can create.

We don't recommend using SysReptor Labs for commercial pentesting reports. We don't guarantee the same level of confidentiality and availability as in SysReptor Cloud, and there is no legal basis for data processing.
:::

</div>


<div class="faq-item">

::: details I signed up for writing exam reports at labs.sysre.pt. When will you delete my data?
SysReptor Labs accounts and exam report data at [labs.sysre.pt](https://labs.sysre.pt) are **deleted after three months without login**.

Export your reports before that (PDF and/or project export) if you need to keep a copy.

We'll send you a warning a few days before account deletion.
:::

</div>


<div class="faq-item">

::: details Can I create a backup of my SysReptor exam reports on labs.sysre.pt?
You can keep copies of your work:

1. **Download the PDF** from the project’s publish page (the rendered exam report).
2. **Export the project** from the projects list (`.tar.gz` archive). That archive can be imported into other SysReptor installations later.

Do this before the account is deleted after three months without login.
:::

</div>


<div class="faq-item" id="labs-login">

::: details I cannot log into my labs.sysre.pt account. What should I do?
If you cannot log into SysReptor at [labs.sysre.pt](https://labs.sysre.pt):

* Confirm you are on [labs.sysre.pt](https://labs.sysre.pt).
* Use [Forgot Password](https://labs.sysre.pt/login/forgot-password/) function and check the email address of your labs account (including spam).

If you had an account previously, your account might have been deleted if you haven't logged in for more than 3 months.
:::

</div>


<div class="faq-item">

::: details Can I self-host SysReptor instead of using SysReptor Labs for exam reports?
Yes. You can [install SysReptor](/setup/installation) on your own server and import the official HTB or OffSec designs. See [how to import HTB or OffSec designs](#import-cert-designs).
:::

</div>


<div class="faq-item" id="import-cert-designs">

::: details How do I get HTB or OffSec report designs into a self-hosted SysReptor?

Import Hack The Box designs and demo projects:

```shell
cd sysreptor/deploy
curl -s "https://docs.sysreptor.com/assets/htb-designs.tar.gz" | docker compose exec --no-TTY app python3 manage.py importdemodata --type=design
curl -s "https://docs.sysreptor.com/assets/htb-demo-projects.tar.gz" | docker compose exec --no-TTY app python3 manage.py importdemodata --type=project
```

Import OffSec designs and demo projects:

```shell
cd sysreptor/deploy
curl -s "https://docs.sysreptor.com/assets/offsec-designs.tar.gz" | docker compose exec --no-TTY app python3 manage.py importdemodata --type=design
curl -s "https://docs.sysreptor.com/assets/offsec-demo-projects.tar.gz" | docker compose exec --no-TTY app python3 manage.py importdemodata --type=project
```

Find more details at [HTB reporting](/htb-reporting-with-sysreptor) and [OffSec reporting](/offsec-reporting-with-sysreptor).
:::

</div>

::: info <DocBadge icon="mdi:help-circle" class="lg middle" label="Further questions?" />
Need help or have questions? Get support and [connect with us and the SysReptor community](https://github.com/Syslifters/sysreptor/discussions/).
:::
