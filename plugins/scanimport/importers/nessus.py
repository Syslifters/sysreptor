import textwrap

from sysreptor.pentests import cvss
from sysreptor.pentests.models import (
    FindingTemplateTranslation,
    Language,
    ProjectNotebookPage,
)
from sysreptor.utils.utils import groupby_to_dict

from ..utils import cvss2_to_cvss31, parse_xml, render_template_string, xml_to_dict
from .base import BaseImporter, fallback_template


class NessusImporter(BaseImporter):
    id = 'nessus'

    fallback_templates = [fallback_template(tags=[f'scanimport:{id}'], translations=[
        FindingTemplateTranslation(
            language=Language.ENGLISH_US,
            custom_fields={
                'summary': '<!--{{ synopsis }}-->',
                'description': textwrap.dedent("""\
                    <!--{{ description }}-->

                    <!--{% for o in plugin_output %}-->
                    ```
                    <!--{{ o }}-->
                    ```
                    <!--{% endfor %}-->
                    """)
            },
        ),
    ])]

    def is_format(self, file):
        tree = parse_xml(file)
        version = tree.xpath('/NessusClientData_v2/Report')
        return bool(version)

    def parse_nessus_findings(self, files):
        findings = []
        for file in files:
            for report_item in parse_xml(file).xpath('/NessusClientData_v2/Report/ReportHost/ReportItem'):
                finding = xml_to_dict(
                    node=report_item, 
                    elements_str=['description', 'solution', 'synopsis', 'risk_factor', 'cve', 'cvss_vector', 'plugin_name'],
                ) | {
                    'plugin_output': report_item.xpath('plugin_output/text()'),
                    'see_also': report_item.xpath('see_also/text()'),
                } | dict(report_item.attrib)

                # Fix text indentation
                for k, v in finding.items():
                    if isinstance(v, str):
                        lines = v.splitlines()
                        if len(lines) > 1:
                            finding[k] = textwrap.dedent(lines[0]) + "\n" + textwrap.dedent('\n'.join(lines[1:]))

                # Exclude snoozed
                if finding.get('snoozed'):
                    continue

                # Parse host
                report_host = report_item.getparent()
                host = {
                    'name': report_host.attrib.get('name')
                }
                for host_tag in report_host.xpath('HostProperties/tag'):
                    tag_name = host_tag.attrib.get('name')
                    tag_value = host_tag.text
                    if tag_name:
                        host[tag_name.replace('-', '_')] = tag_value
                finding['host'] = host

                # Format finding data
                finding['title'] = finding.get('pluginName') or finding.get('plugin_name')
                finding['severity'] = (finding.pop('risk_factor', None) or 'info').lower()
                if finding['severity'] not in self.severity_mapping:
                    finding['severity'] = 'info'
                finding['severity_score'] = int(report_item.attrib.get('severity') or 0) + 1
                finding['cvss'] = cvss2_to_cvss31(finding.get('cvss_vector'))

                finding['recommendation'] = finding.pop('solution', '')
                finding['references'] = []
                for ref in finding.pop('see_also', []):
                    finding['references'].extend(list(filter(None, ref.splitlines())))
                
                target = host.get("name") or host.get("host_ip") or "n/a"
                port = finding.get("port") or "0"
                svc_name = finding.get("svc_name") or "general"
                finding['affected_components'] = [
                    f"{target}{':' + port if port != '0' else ''}{' (' + svc_name + ')' if svc_name != 'general' else ''}"
                ]
                
                findings.append(finding)

        findings = sorted(findings, key=lambda f: cvss.calculate_score(f['cvss']) if f['cvss'] else f['severity_score'])
        return findings
    
    def merge_findings_by_plugin(self, findings):
        out = []
        for _, findings in groupby_to_dict(findings, key=lambda f: f['pluginID']).items():
            merged = findings[0]
            for f in findings[1:]:
                merged['affected_components'] += f['affected_components']
                merged['references'] = list(set(merged['references'] + f['references']))
                merged['plugin_output'] += f['plugin_output']
            out.append(merged)
        return out

    def parse_notes(self, files):
        notes = []
        note_root = ProjectNotebookPage(
            title='Nessus',
            icon_emoji='🛡️',
        )
        notes.append(note_root)

        order = 0
        for host, findings in groupby_to_dict(self.parse_nessus_findings(files), key=lambda f: f['host']['name']).items():
            order += 1
            note_host = ProjectNotebookPage(
                parent=note_root,
                order=order,
                checked=False,
                title=host,
                text=render_template_string(textwrap.dedent(
                    """\
                    # Nessus Scan
                    *<!--{{ HOST_START }}--> - <!--{{ HOST_END }}-->*

                    **IP:** <!--{{ host_ip }}-->  
                    **NetBIOS Name:** <!--{{ netbios_name|default:"n/a" }}-->  
                    **OS:** <!--{{ operating_system|default:"n/a" }}-->

                    ## Vulnerability overview
                    
                    | Title | Severity |
                    | ------- | ------- |
                    <!--{% for f in findings %}-->| <!--{{ f.title }}--> | <!--{{ f.severity }}--> |
                    <!--{% endfor %}-->
                    """), context=findings[0]['host'] | {'findings': findings})
            )
            notes.append(note_host)
            for idx, finding in enumerate(self.merge_findings_by_plugin(findings)):
                notes.append(ProjectNotebookPage(
                    parent=note_host,
                    order=idx + 1,
                    checked=False,
                    title=self.severity_mapping.get(finding['severity'], '') + ' ' + finding['title'],
                    text=render_template_string(textwrap.dedent(
                        """\
                        **Plugin ID:** <!--{{ pluginID }}-->  
                        **Severity:** <!--{{ severity }}-->  
                        **Port:** <!--{{ port }}-->  
                        **Service:** <!--{{ svc_name|default:"n/a" }}-->  

                        <!--{% for o in plugin_output %}-->
                        ```
                        <!--{{ o }}-->
                        ```
                        <!--{% endfor %}-->

                        ## Description
                        <!--{{ description }}-->

                        ## Solution
                        <!--{{ recommendation }}-->
                        """), context=finding),
                ))
        return notes

    def parse_findings(self, files, project):
        findings = []
        templates = self.get_all_finding_templates()
        for issue in self.merge_findings_by_plugin(self.parse_nessus_findings(files)):
            findings.append(self.generate_finding_from_template(
                project=project,
                tr=self.select_finding_template(
                    templates=templates,
                    fallback=self.fallback_templates,
                    selector=issue.get('pluginID'),
                    language=project.language,
                ),
                data=issue,
            ))

        return findings

