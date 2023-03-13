import operator
import yaml
import requests
import os
import sys

SOFTWARE_FILE = 'reporting_software.yml'
DOCUMENT_CONTENT = '''---
{metadata}
search:
  exclude: true
---

# {title}

{preface}
<br>

{table}

{postface}
'''

ALTERNATIVE_TO_PREFACE = '''
Similar projects and and alternatives to [{name}]({url}){{target=_blank}} Penetration Test Reporting Tool.

'''

PREFACE = '''
SysReptor is a Pentest Reporting Tool written by pentesters, for pentesters. It is built with security in mind, best usability and strongest focus on the needs of pentesters.

However, if it does not fit your needs, here is a list of alternative tools.  
'''

TABLE_HEADER = '''| Name | Report Customization | Deployment | Costs/User/Month |
| - | - | - | - |'''
TABLE_ROW = '''| {software_icon} [{name}]({url}){{target=_blank}} | :material-file-document: {customization} | :material-server: {deployment} | :material-tag: {price} |
'''
POSTFACE = """
<br><div style="text-align:center">[:rocket: Sign Up to SysReptor](#){ .md-button .no-print target="_blank" }</div>
<br>
This overview of penetration testing reporting tools has been compiled to the best of our knowledge and belief. We do not guarantee that the information is correct or up-to-date.

❌ We regard software projects without updates for one year, with missing security patches or major dependencies without support as discontinued.

We welcome tips on other pentest reporting tools.
For inquiries and tips write us a short message to hello@syslifters.com.
"""

def generate_software_lists(*args, **kwargs):
    ret = 0
    software_list = get_software()
    if not kwargs.get('config', dict()).get('site_url'):
        # Check links at deployment time
        # site_url is empty during gh-deploy, at server it is 127.0.0.1:8000
        ret = check_url_availability(software_list)

    if not need_regenerate(software_list):
        sys.exit(ret)

    # Generate "Pentest Reporting Tools" page
    title = f"Pentest Reporting Tools - A List of the most popular tools"
    metadata = f"title: {title}"
    preface = PREFACE
    table = generate_table(software_list)
    postface = POSTFACE
    document = DOCUMENT_CONTENT.format(
        metadata=metadata,
        title=title,
        preface=preface,
        table=table,
        postface=postface
    )
    # write document
    with open("docs/s/pentest-reporting-tools.md", 'w', encoding='utf-8') as f:
        f.write(document)

    # Generate "Alternative To Pages"
    for software in software_list:
        if software.get('self'):
            # No alternative to us page
            continue
        title = f"Alternatives to {software['name']} Pentesting Reporting Tool"
        metadata = f'''title: {title.format(name=software['name'])}'''
        title = title.format(name=f"**{software['name']}")
        preface = ALTERNATIVE_TO_PREFACE.format(
            name=software['name'],
            url=software['url'],
        ) + PREFACE
        table = generate_table(software_list)
        postface = POSTFACE

        if not table:
            # If no table generated, do not create page
            continue

        document = DOCUMENT_CONTENT.format(
            metadata=metadata,
            title=title,
            preface=preface,
            table=table,
            postface=postface
        )

        # write document
        with open(get_filename(software['name']), 'w', encoding='utf-8') as f:
            f.write(document)

    sys.exit(ret)


def get_filename(name):
    replace_chars = [
        ('/', '-'),
        (' ', '-'),
        ('.', ''),
        ('ö', 'oe'),
        ('ä', 'ae'),
        ('ü', 'ue'),
        ('ß', 'ss'),
    ]
    name = name.lower()
    for replace in replace_chars:
        name = name.replace(replace[0], replace[1])
    return f'docs/s/alternative-to-{name}-reporting-tool.md'


def need_regenerate(software_list):
    oldest_md_mtime = float('inf')
    for software in software_list:
        try:
            oldest_md_mtime = min(os.path.getmtime(
                get_filename(software['name'])), oldest_md_mtime)
        except FileNotFoundError:
            return True
    list_mtime = os.path.getmtime(SOFTWARE_FILE)
    script_mtime = os.path.getmtime(os.path.realpath(__file__))
    if list_mtime > oldest_md_mtime or script_mtime > oldest_md_mtime:
        return True


def sort_software(software):
    # Filter out empty entries
    software_list = [c for c in software if c['name']]
    for software in software_list:
        if 'self' not in software:
            software['self'] = False
        if 'discontinued' not in software:
            software['discontinued'] = False
        if 'url' not in software:
            raise KeyError(f"No url specified for {software['name']}")
        if 'price' not in software:
            raise KeyError(f"No price specified for {software['name']}")

    software_list.sort(key=lambda k: (k['name'].lower()))
    software_list.sort(key=operator.itemgetter('discontinued'), reverse=False)
    software_list.sort(key=operator.itemgetter('self'), reverse=True)
    return software_list


def get_software():
    # Read all software
    with open(SOFTWARE_FILE, 'r', encoding='utf-8') as f:
        software = yaml.safe_load(f).get('software')

    software = sort_software(software)
    return software


def check_url_availability(software_list):
    errors = 0
    for s in software_list:
        try:
            r = requests.head(s['url'], timeout=4, headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        except requests.exceptions:
            errors += 1
            print(f"{r.status_code} URL for {s['name']} ist not reachable: {s['url']}")
        if r.status_code >= 400:
            errors += 1
            print(f"{r.status_code} URL for {s['name']} ist not reachable: {s['url']}")
    if errors:
        return 127


def generate_table(software_list, skip_software=None):
    table_rows = list()
    for software in software_list:
        software_icon = ""
        if software.get('self'):
            software_icon = "🔥"
        elif software.get('discontinued'):
            software_icon = '❌'
        cons_icon = ":material-arrow-down-box:" if not software.get('discontinued') else ':octicons-x-circle-fill-12:{ style="color: #e21212;" }'

        table_row = TABLE_ROW.format(
            software_icon=software_icon,
            name=software['name'],
            url=software['url'],
            pros=software['pros'] if software['pros'] else '',
            cons_icon=cons_icon,
            cons=software['cons'] if software['cons'] else '',
            customization=software['customization'] if software['customization'] else '',
            deployment=software['deployment'] if software['deployment'] else '',
            price=software['price'] if software['price'] else "",
        )
        
        if software['name'] != skip_software:
            table_rows.append(table_row)

    table = None
    if table_rows:
        table = f"{TABLE_HEADER}\n{''.join(table_rows)}"
    return table
