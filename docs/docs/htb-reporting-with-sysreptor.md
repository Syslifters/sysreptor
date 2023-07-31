# Hack The Box Reporting

Use our cloud service for free to write your Hack The Box CPTS or CBBH reports.

💲 Free  
📝 Write in markdown  
⚙️ Render your report to PDF  
🛡️ CPTS, CBBH 
🚀 Fully customizable  
🎉 No need for Word  
👌 No local software troubleshooting

<br><div style="text-align:center">[:rocket: Sign Up Now](https://htb.sysreptor.com/htb/signup/){ .md-button }</div>
<br><div style="text-align:center">Already have an account? [Login here.](https://labs.sysre.pt){ target=_blank }</div>
<br>

## Prefer self-hosting?
1. [Install](/setup/installation/){ target="_blank" } SysReptor
2. Import all HTB Designs:

```shell linenums="1"
cd sysreptor/deploy
url="https://docs.sysreptor.com/assets/htb-designs.tar.gz"
curl -s "$url" | docker compose exec --no-TTY app python3 manage.py importdemodata --type=design
```

<br><br>

## Hack The Box Report Templates*
### Penetration Testing
<div style="text-align:center">
<a href="/assets/reports/HTB-CPTS-Report.pdf" target="_blank">
    <figure style="float:left;width:24%;margin:0.5em;">
        <img alt="HTB CPTS Report Demo" src="/assets/reports/HTB-CPTS-Report-Preview.png" style="border:1px solid;" />
        <figcaption>HTB CPTS Report Demo</figcaption>
    </figure>
</a>
</div>
<br style="clear:both" />

## Creating an HTB CPTS Report
<figure markdown>
  ![CPTS Reporting Procedure](/images/htb-reporting.gif)
</figure>