# OffSec Reporting

Use our cloud service for free to write your OffSec OSCP, OSWP, OSEP, OSWA, OSWE, OSED, OSMR, OSEE, OSDA reports.

💲 Free  
📝 Write in markdown  
⚙️ Render your report to PDF  
🛡️ OSCP, OSWP, OSEP, OSWA, OSWE, OSED, OSMR, OSEE, OSDA  
🚀 Fully customizable  
🎉 No need for Word  
👌 No local software troubleshooting

<br><div style="text-align:center">[:rocket: Sign Up Now (it's free)](https://oscp.sysreptor.com/oscp/signup/){ .md-button }</div>
<br><div style="text-align:center">Already have an account? [Login here.](https://labs.sysre.pt){ target=_blank }</div>
<br>

## Prefer self-hosting?
1. [Install](/setup/installation/){ target="_blank" } SysReptor
2. Import all OffSec Designs:

```shell linenums="1"
cd sysreptor/deploy
url="https://docs.sysreptor.com/assets/offsec-designs.tar.gz"
curl -s "$url" | docker compose exec --no-TTY app python3 manage.py importdemodata --type=design
```

<br><br>

## OffSec Report Templates*
### Penetration Testing
<div style="text-align:center">
<a href="/assets/reports/OSCP-Exam-Report.pdf" target="_blank">
    <figure style="float:left;width:24%;margin:0.5em;">
        <img alt="OSCP Exam Report Demo" src="/assets/reports/OSCP-Exam-Report-Preview.png" style="border:1px solid;" />
        <figcaption>OSCP Exam Report Demo</figcaption>
    </figure>
</a>
<a href="/assets/reports/OSCP-Lab-Report.pdf" target="_blank">
    <figure style="float:left;width:24%;margin:0.5em;">
        <img alt="OSCP Lab Report Demo" src="/assets/reports/OSCP-Lab-Report-Preview.png" style="border:1px solid;" />
        <figcaption>OSCP Lab Report Demo</figcaption>
    </figure>
</a>
<a href="/assets/reports/OSWP-Exam-Report.pdf" target="_blank">
    <figure style="float:left;width:24%;margin:0.5em;">
        <img alt="OSWP Exam Report Demo" src="/assets/reports/OSWP-Exam-Report-Preview.png" style="border:1px solid;" />
        <figcaption>OSWP Exam Report Demo</figcaption>
    </figure>
</a>
<a href="/assets/reports/OSEP-Exam-Report.pdf" target="_blank">
    <figure style="float:left;width:24%;margin:0.5em;">
        <img alt="OSEP Exam Report Demo" src="/assets/reports/OSEP-Exam-Report-Preview.png" style="border:1px solid;" />
        <figcaption>OSEP Exam Report Demo</figcaption>
    </figure>
</a>
</div>
<br style="clear:both" />

### Web Application
<div style="text-align:center">
<a href="/assets/reports/OSWA-Exam-Report.pdf" target="_blank">
    <figure style="float:left;width:24%;margin:0.5em;">
        <img alt="OSWA Exam Report Demo" src="/assets/reports/OSWA-Exam-Report-Preview.png" style="border:1px solid;" />
        <figcaption>OSWA Exam Report Demo</figcaption>
    </figure>
</a>
<a href="/assets/reports/OSWE-Exam-Report.pdf" target="_blank">
    <figure style="float:left;width:24%;margin:0.5em;">
        <img alt="OSWE Exam Report Demo" src="/assets/reports/OSWE-Exam-Report-Preview.png" style="border:1px solid;" />
        <figcaption>OSWE Exam Report Demo</figcaption>
    </figure>
</a>
</div>
<br style="clear:both" />

### Exploit Development
<div style="text-align:center">
<a href="/assets/reports/OSED-Exam-Report.pdf" target="_blank">
    <figure style="float:left;width:24%;margin:0.5em;">
        <img alt="OSED Exam Report Demo" src="/assets/reports/OSED-Exam-Report-Preview.png" style="border:1px solid;" />
        <figcaption>OSED Exam Report Demo</figcaption>
    </figure>
</a>
<a href="/assets/reports/OSMR-Exam-Report.pdf" target="_blank">
    <figure style="float:left;width:24%;margin:0.5em;">
        <img alt="OSMR Exam Report Demo" src="/assets/reports/OSMR-Exam-Report-Preview.png" style="border:1px solid;" />
        <figcaption>OSMR Exam Report Demo</figcaption>
    </figure>
</a>
<a href="/assets/reports/OSEE-Exam-Report.pdf" target="_blank">
    <figure style="float:left;width:24%;margin:0.5em;">
        <img alt="OSEE Exam Report Demo" src="/assets/reports/OSEE-Exam-Report-Preview.png" style="border:1px solid;" />
        <figcaption>OSEE Exam Report Demo</figcaption>
    </figure>
</a>
</div>
<br style="clear:both" />

### Security Operations
<div style="text-align:center">
<a href="/assets/reports/OSDA-Exam-Report.pdf" target="_blank">
    <figure style="float:left;width:24%;margin:0.5em;">
        <img alt="OSDA Exam Report Demo" src="/assets/reports/OSDA-Exam-Report-Preview.png" style="border:1px solid;" />
        <figcaption>OSDA Exam Report Demo</figcaption>
    </figure>
</a>
</div>

<br style="clear:both" />
*The cover pages are based on <a href="https://twitter.com/noraj_rawsec" target="_blank">noraj</a>'s great <a href="https://github.com/noraj/OSCP-Exam-Report-Template-Markdown" target="_blank">OSCP LaTeX templates</a>. The structure follows the official OffSec reports (with kind permission by OffSec).

## Creating an OSCP Exam Report
<figure markdown>
  ![OSCP Reporting Procedure](/images/oscp-reporting.gif)
</figure>

<br><div style="text-align:center">
    Not happy with our solution?<br><br>
    [:material-tools: Check out alternatives](/oscp-reporting-tools/){ .md-button target="_blank" }
</div>
