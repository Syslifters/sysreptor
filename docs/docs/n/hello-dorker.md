---
exclude: yes
title: ""
search:
  exclude: true
---

<h1></h1>
<div style="text-align: center;">
    We have no <span id="filename" style="font-size:1.5rem"></span> for you.<br>

    But an awesome <span style="font-size:1.5rem">Pentest Reporting tool</span>.
</div>
<br><br>
<img 
    style="display: block; 
           margin-top: 3rem;
           margin-left: auto;
           margin-right: auto;
           filter: invert(1);"
    src="/images/logo.svg"
    viewBox="0 0 120 120"
    height="120"
    width="120"
    alt="SysReptor Dino Logo">
</img>

<div style="text-align: center;">
    SysReptor makes Pentest Reporting easy.<br>
    Design your report in HTML.<br>
    Render to PDF.<br>
    On-Premises.<br>
    Or Cloud.<br>
    <span style="color:red">❤</span>
</div>

<br><div style="text-align:center">[:rocket: Get it for Free](../features-and-pricing.md){ .md-button }</div>

<figure markdown>
  ![Create finding from template](../images/create_finding_from_template.gif)
  <figcaption>Create finding from template</figcaption>
</figure>

<figure markdown>
  ![Export report as PDF](../images/export_project.gif)
  <figcaption>Export report as PDF</figcaption>
</figure>

<script>
    const allowed_names = [
        '.bashrc',
        '.bash_profile',
        '.env',
        '.ssh/',
        'access_token.json',
        'admin-login.php',
        'after.sh',
        'awstats',
        'backup.db',
        'backup.sql',
        'catalina.out',
        'cloud-config.yaml',
        'cloud-config.yml',
        'configure.sh',
        'cookies.php',
        'cv.pdf',
        'database.sql.zip',
        'db.py',
        'deploy.sh',
        'httpclient/',
        'human_resources/',
        'id_rsa',
        'keystore.jks',
        'login/',
        'passwords.html',
        'phonepe',
        'printenv.pl',
        'private_key.pem',
        'pwd.db',
        'pyvenv.cfg',
        'release.sh',
        'repository/',
        'resume.pdf',
        'secret.sql',
        'setup.sh',
        'setup_db.sh',
        'transaction/',
        'venv/',
        'wp-admin',
        'wp-admin.zip',
        'wp-content/'
    ];
    let fragment = window.location.hash.slice(1);
    if (allowed_names.indexOf(fragment) === -1) {
        fragment = 'sensitive file';
    }

    document.getElementById("filename").innerHTML = fragment;
</script>