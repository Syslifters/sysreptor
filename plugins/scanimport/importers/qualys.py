import textwrap
from urllib.parse import urlparse

from sysreptor.pentests import cvss
from sysreptor.pentests.models import (
    FindingTemplateTranslation,
    Language,
    ProjectNotebookPage,
)
from sysreptor.utils.utils import groupby_to_dict

from ..utils import parse_xml, render_template_string, xml_to_dict
from .base import BaseImporter, fallback_template


class QualysImporter(BaseImporter):
    id = 'qualys'

    fallback_templates = [fallback_template(tags=[f'scanimport:{id}'], translations=[
        FindingTemplateTranslation(
            language=Language.ENGLISH_US,
            custom_fields={
                'summary': '<!--{{ issueBackground }}-->',
                'description': '<!--{{ issueDetail }}-->',
                'recommendation': '<!--{{ remediationBackground }}-->',
            },
        ),
    ])]

    def is_format(self, file):
        tree = parse_xml(file)
        return bool(tree.xpath('/SCAN')) or bool(tree.xpath('/WAS_SCAN_REPORT'))
    
    def parse_qualys_findings(self, files):
        findings = []
        for file in files:
            tree =  parse_xml(file)

            for vuln_xml in tree.xpath('/SCAN/IP/VULNS/CAT/VULN'):
                vuln_data = xml_to_dict(
                    node=vuln_xml,
                    elements_str=['TITLE', 'DIAGNOSIS', 'CONSEQUENCE', 'SOLUTION', 'SEVERITY', 'RESULT'],
                ) | dict(vuln_xml.attrib)
                finding = {k.lower(): v for k, v in vuln_data.items()} | dict(vuln_xml.attrib)

                cat_xml = vuln_xml.getparent()
                ip_xml = cat_xml.getparent().getparent()
                target = {
                    'ip': ip_xml.attrib.get('value'), 
                    'hostname': ip_xml.attrib.get('name'),
                    'port': cat_xml.attrib.get('port'),
                    'protocol': cat_xml.attrib.get('protocol'), 
                }
                finding['target'] = target
                finding['affected_components'] = [(target['hostname'] or target['ip']) + (f":{target['port']}" if target['port'] else '')]

                finding['severity_score'] = int(finding.get('severity') or 1)
                finding['severity'] = list(cvss.CVSSLevel)[finding['severity_score'] - 1]
                finding['description'] = finding.pop('diagnosis', None)
                finding['summary'] = finding.pop('consequence', None)
                finding['recommendation'] = finding.pop('solution', None)

                findings.append(finding)

            qids = {
                q.find('QID').text: xml_to_dict(
                    node=q,
                    elements_str=['QID', 'TITLE', 'SEVERITY', 'CATEGORY', 'DESCRIPTION', 'IMPACT', 'SOLUTION', 'CWE']
                ) for q in tree.xpath('/WAS_SCAN_REPORT/GLOSSARY/QID_LIST/QID')
            }
            for vuln_xml in tree.xpath('/WAS_SCAN_REPORT/RESULTS/VULNERABILITY_LIST/VULNERABILITY'):
                finding = xml_to_dict(node=vuln_xml, elements_str=['QID', 'URL', 'SEVERITY'])
                finding = qids[finding['QID']] | finding | {'number': finding['QID']}
                finding = {k.lower(): v for k, v in finding.items()}
                
                url = urlparse(finding['url'])
                finding['target'] = {
                    'ip': None,
                    'hostname': url.hostname,
                    'port': url.port if url.port else (443 if url.scheme == 'https' else 80),
                    'protocol': 'tcp',
                }
                finding['affected_components'] = [finding['url']]
                finding['severity_score'] = int(finding['severity'] or 1)
                finding['severity'] = list(cvss.CVSSLevel)[finding['severity_score'] - 1]
                finding['summary'] = finding.pop('impact', None)
                finding['recommendation'] = finding.pop('solution', None)

                findings.append(finding)

        # Order by severity
        findings = sorted(findings, key=lambda x: (x.get("severity_score", 0) * -1, x.get('title', '')))
        return findings
    
    def merge_findings(self, findings: list[dict]) -> list:
        out = []
        for findings_group in groupby_to_dict(findings, key=lambda x: x.get('number', '')).values():
            merged = findings_group[0]
            for f in findings_group[1:]:
                merged['affected_components'].extend(f['affected_components'])
            out.append(merged)

        out = sorted(out, key=lambda x: (x.get("severity_score", 0) * -1, x.get('title', '')))
        return out

    def parse_notes(self, files):
        notes = []

        # Main note
        note_root = ProjectNotebookPage(
            icon_emoji='🛡️',
            title='Qualys',
            text=''
        )
        notes.append(note_root)

        order = 0
        for hostname, issues in groupby_to_dict(self.parse_qualys_findings(files), key=lambda f: f['target'].get('hostname') or f['target'].get('ip')).items():
            order += 1
            note_host = ProjectNotebookPage(
                parent=note_root,
                order=order,
                checked=False,
                title=hostname,
                text=render_template_string(textwrap.dedent(
                    """\
                    **Target:** <!--{{ hostname }}-->  

                    ## Vulnerability overview

                    | Title | Severity |
                    | ------- | ------- |
                    <!--{% for f in data %}-->| <!--{{f.title}}--> | <!--{{f.severity_label}}--> |
                    <!--{% endfor %}-->
                    """), { 'hostname': hostname, 'findings': issues }),
            )
            notes.append(note_host)
            for idx, issue in enumerate(self.merge_findings(issues)):
                notes.append(ProjectNotebookPage(
                    parent=note_host,
                    order=idx + 1,
                    checked=False,
                    title=f"{self.severity_mapping.get(issue.get('severity', 'info').lower())} {issue.get('title', '')}",
                    text=render_template_string(textwrap.dedent(
                        """\
                        <!--{% if qid %}-->**QID:** <!--{{ qid }}-->  <!--{% endif %}-->
                        **Severity:** <!--{{ severity }}-->
                        <!--{% if cwe %}-->**CWE:** <!--{{ cwe }}-->  <!--{% endif %}-->
                        <!--{% if url %}-->**URL:** <!--{{ url }}-->  <!--{% endif %}-->
                        <!--{% if target.ip %}-->**IP:** <!--{{ target.ip }}-->  <!--{% endif %}-->
                        <!--{% if detection_date %}-->**Detected:** <!--{{ detection_date }}-->  <!--{% endif %}-->

                        ## Description
                        <!--{{ description }}-->

                        <!--{% if summary %}--><!--{{ summary }}--><!--{% endif %}-->

                        ## Solution
                        <!--{{ recommendation }}-->
                        """), issue),
                ))

        if len(notes) == 1:
            # Only root note: nothing to add
            return []
        return notes

    def parse_findings(self, files, project):
        findings = []
        templates = self.get_all_finding_templates()
        for issue in self.merge_findings(self.parse_qualys_findings(files)):
            findings.append(self.generate_finding_from_template(
                tr=self.select_finding_template(
                    templates=templates,
                    fallback=self.fallback_templates,
                    selector=issue.get('number'),
                    language=project.language,
                ),
                data=issue,
                project=project,
            ))

        return findings

