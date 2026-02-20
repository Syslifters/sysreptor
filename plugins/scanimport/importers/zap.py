import json
import textwrap

from sysreptor.pentests.models import (
    FindingTemplateTranslation,
    Language,
    ProjectNotebookPage,
)
from sysreptor.utils.utils import groupby_to_dict, is_json_string

from ..utils import parse_xml, render_template_string, xml_to_dict
from .base import BaseImporter, fallback_template


class ZapImporter(BaseImporter):
    id = 'zap'

    fallback_templates = [fallback_template(tags=[f'scanimport:{id}'], translations=[
        FindingTemplateTranslation(
            language=Language.ENGLISH_US,
            custom_fields={
                'summary': textwrap.dedent(
                    """\
                    <!-- This is a finding from ZAP Alert Reference <!--{{ alertRef }}--> -->

                    <!--{{ desc }}-->
                    """),
                'description': '<!--{{ otherinfo }}-->',
                'recommendation': '<!--{{ solution }}-->',
            },
        ),
    ])]

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
                alert_dict = xml_to_dict(
                    node=alert_xml,
                    elements_str=['pluginid', 'name', 'alert', 'alertRef', 'riskcode', 'confidence', 'desc', 'otherinfo', 'solution', 'cweid'],
                ) | {
                    'site': dict(site_xml.attrib),
                    'instances': [xml_to_dict(
                        node=instance_xml,
                        elements_str=['uri', 'method', 'param', 'attack', 'evidence', 'otherinfo', 'requestheader', 'requestbody', 'responseheader', 'responsebody'],
                    ) for instance_xml in alert_xml.xpath('instances/instance')],
                }
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
            alert['alertRef'] = alert.get('alertRef') or '0'
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

    def parse_findings(self, files, project):
        findings = []
        templates = self.get_all_finding_templates()
        alerts = self.merge_alerts(self.parse_zap_data(files))
        
        for alert in alerts:
            # Build affected components from instances
            affected_components = []
            for instance in alert.get('instances', []):
                component = instance.get('uri', '')
                if instance.get('param'):
                    component += f" (param: {instance['param']})"
                if component and component not in affected_components:
                    affected_components.append(component)
            
            alert['affected_components'] = affected_components
            alert['title'] = alert.get('name', '')
            alert['cwe'] = alert.get('cweid', '')
            
            findings.append(self.generate_finding_from_template(
                project=project,
                tr=self.select_finding_template(
                    templates=templates,
                    fallback=self.fallback_templates,
                    selector=alert.get('alertRef'),
                    language=project.language,
                ),
                data=alert,
            ))

        return findings

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
                    | Site   | <!--{{ name }}--> |
                    | Host   | <!--{{ host }}--> |
                    | Port   | <!--{{ port }}--> |
                    | SSL?   | <!--{{ ssl|yesno }}--> |
                    """), context=alerts[0]['site']),
            )
            notes.append(note_host)
            merged_alerts = sorted(self.merge_alerts(alerts), key=lambda a: int(a['riskcode']), reverse=True)
            for idx, alert in enumerate(merged_alerts):
                notes.append(ProjectNotebookPage(
                    parent=note_host,
                    order=idx + 1,
                    checked=False,
                    title=f"{self.severity_mapping.get(alert['severity'], '')} {alert['name']}",
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
