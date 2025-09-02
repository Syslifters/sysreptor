import json
import textwrap

from sysreptor.pentests.models import (
    ProjectNotebookPage,
)
from sysreptor.utils.utils import groupby_to_dict, is_json_string

from ..utils import parse_xml, render_template_string, xml_to_dict
from .base import BaseImporter


class ZapImporter(BaseImporter):
    id = 'zap'

    def is_format(self, file):
        file.seek(0)
        data_str = file.read()
        if is_json_string(data_str) and (data := json.loads(data_str)) and isinstance(data, dict) and data.get('@programName') == 'OWASP ZAP':
            return True
        elif parse_xml(file).xpath('/OWASPZAPReport/@programName') == ['OWASP ZAP']:
            return True
        return False

    def parse_zap_xml(self, file):
        alerts = []
        for site_xml in parse_xml(file).xpath('/OWASPZAPReport/site'):
            for alert_xml in site_xml.xpath('alerts/alertitem'):
                alert_dict = xml_to_dict(alert_xml) | {
                    'site': dict(site_xml.attrib),
                }
                if isinstance(alert_dict.get('instances'), dict):
                    alert_dict['instances'] = [alert_dict['instances']]
                alerts.append(alert_dict)
        return alerts

    
    def parse_zap_json(self, file):
        alerts = []
        file.seek(0)
        for site in json.loads(file.read()).get('site', []):
            for alert in site.get('alerts', []):
                alerts.append(alert | {
                    'site': {k: site.get(f'@{k}') for k in ['name', 'host', 'port', 'ssl']},
                })
        return alerts

    def parse_zap_data(self, files):
        alerts = []
        for file in files:
            try:
                alerts.extend(self.parse_zap_json(file))
            except json.JSONDecodeError:
                alerts.extend(self.parse_zap_xml(file))

        for alert in alerts:
            alert['riskcode'] = alert.get('riskcode') or '0'
            alert['severity'] = {'0': 'info', '1': 'low', '2': 'medium', '3': 'high'}.get(alert['riskcode'], 'info')
        alerts = sorted(alerts, key=lambda a: (a['riskcode'], a['alertRef']))

        return alerts
    
    def merge_alerts(self, alerts):
        out = []
        for alert_group in groupby_to_dict(alerts, key=lambda a: a.get('alertRef', '')).values():
            merged = alert_group[0]
            for alert in alert_group[1:]:
                merged['instances'] = merged.get('instances', []) + alert.get('instances', [])
                merged['count'] = len(merged['instances'])
            out.append(merged)
        return out


    def parse_notes(self, files):
        notes = []

        note_root = ProjectNotebookPage(
            icon_emoji='🌩️',
            title='Zap',
        )
        notes.append(note_root)

        order = 0
        for url, alerts in groupby_to_dict(self.parse_zap_data(files), key=lambda a: a['site']['name']).items():
            order += 1
            note_host = ProjectNotebookPage(
                parent=note_root,
                order=order,
                checked=False,
                title=url,
                text=render_template_string(textwrap.dedent(
                    """\
                    | Target | Information |
                    | :----- | :---------- |
                    | Site   | <!--{{name}}--> |
                    | Host   | <!--{{host}}--> |
                    | Port   | <!--{{port}}--> |
                    | SSL?   | <!--{{ssl|yesno}}--> |
                    """), context={}),
            )
            notes.append(note_host)
            for idx, alert in enumerate(self.merge_alerts(alerts)):
                notes.append(ProjectNotebookPage(
                    parent=note_host,
                    order=idx + 1,
                    checked=False,
                    title=f"{self.severity_mapping.get(alert['riskcode'], '')} {alert['name']}",
                    text=render_template_string(textwrap.dedent(
                        """\
                        | Target | Information |
                        | :--- | :--- |
                        | Risk | <!--{{riskdesc}}--> |
                        | Number of Affected Instances | <!--{{count}}--> |
                        | CWE | [<!--{{cweid}}-->](https://cwe.mitre.org/data/definitions/<!--{{cweid}}-->.html) |

                        **Instances**
                        <!--{% noemptylines %}-->
                        | Method | URI | Param | Payload |
                        | :--- | :--- | :--- | :--- |
                        <!--{% for instance in instances %}-->
                        | <!--{{instance.method}}--> | <!--{{instance.uri}}--> | <!--{{instance.param}}--> | <!--{{instance.attack}}--> |
                        <!--{% endfor %}-->
                        <!--{% endnoemptylines %}-->

                        **Description**

                        <!--{{desc}}-->

                        **Solution**

                        <!--{{solution}}-->

                        <!--{% if reference %}-->**References**

                        <!--{{reference}}-->
                        <!--{% endif %}-->
                        """), context=alert),
                ))
        return notes
