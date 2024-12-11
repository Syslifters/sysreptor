# Hack The Box Reporting

Our free cloud service to write your Hack The Box CPTS, CBBH, and CDSA reports.

💲 Free  
📝 Write in markdown  
⚙️ Render your report to PDF  
🛡️ CPTS, CBBH, CDSA, CWEE, CAPE  
🚀 Fully customizable  
👌 No local software troubleshooting

<br><div style="text-align:center">[:rocket: Sign Up (it's free)](https://htb.sysreptor.com/htb/signup/){ .md-button }</div>
<br><div style="text-align:center">Already have an account? [Login here.](https://labs.sysre.pt){ target=_blank }</div>
<br>

## Prefer self-hosting?
1. [Install](setup/installation.md){ target="_blank" } SysReptor
2. Import all HTB Designs:

```shell
cd sysreptor/deploy
curl -s "https://docs.sysreptor.com/assets/htb-designs.tar.gz" | docker compose exec --no-TTY app python3 manage.py importdemodata --type=design
curl -s "https://docs.sysreptor.com/assets/htb-demo-projects.tar.gz" | docker compose exec --no-TTY app python3 manage.py importdemodata --type=project
```

<br><br>

## Hack The Box Reports
<div style="text-align:center">
<a href="/assets/reports/HTB-CPTS-Report.pdf" target="_blank">
    <figure style="float:left;width:24%;margin:0.5em;">
        <img alt="HTB CPTS Report Demo" src="/assets/reports/HTB-CPTS-Report-Preview.png" style="border:1px solid;" />
        <figcaption>HTB CPTS Report Demo</figcaption>
    </figure>
</a>
<a href="/assets/reports/HTB-CBBH-Report.pdf" target="_blank">
    <figure style="float:left;width:24%;margin:0.5em;">
        <img alt="HTB CBBH Report Demo" src="/assets/reports/HTB-CBBH-Report-Preview.png" style="border:1px solid;" />
        <figcaption>HTB CBBH Report Demo</figcaption>
    </figure>
</a>
<a href="/assets/reports/HTB-CDSA-Report.pdf" target="_blank">
    <figure style="float:left;width:24%;margin:0.5em;">
        <img alt="HTB CDSA Report Demo" src="/assets/reports/HTB-CDSA-Report-Preview.png" style="border:1px solid;" />
        <figcaption>HTB CDSA Report Demo</figcaption>
    </figure>
</a>
<a href="/assets/reports/HTB-CWEE-Report.pdf" target="_blank">
    <figure style="float:left;width:24%;margin:0.5em;">
        <img alt="HTB CWEE Report Demo" src="/assets/reports/HTB-CWEE-Report-Preview.png" style="border:1px solid;" />
        <figcaption>HTB CWEE Report Demo</figcaption>
    </figure>
</a>
<a href="/assets/reports/HTB-CAPE-Report.pdf" target="_blank">
    <figure style="float:left;width:24%;margin:0.5em;">
        <img alt="HTB CAPE Report Demo" src="/assets/reports/HTB-CAPE-Report-Preview.png" style="border:1px solid;" />
        <figcaption>HTB CAPE Report Demo</figcaption>
    </figure>
</a>
</div>
<br style="clear:both" />

## Creating HTB Report
<figure markdown>
  ![CPTS Reporting Procedure](images/cpts-reporting.gif)
</figure>

