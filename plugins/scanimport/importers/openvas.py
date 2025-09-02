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


class OpenVASImporter(BaseImporter):
    id = 'openvas'

    fallback_templates = [fallback_template(tags=[f'scanimport:{id}'], translations=[
        FindingTemplateTranslation(
            language=Language.ENGLISH_US,
            custom_fields={
                'summary': '<!--{{ issueBackground }}-->',
                'description': textwrap.dedent(
                    """\
                    <!-- This is a finding from OID <!--{{ oid }}--> -->

                    <!--{{ impact }}-->

                    <!--{{ insight }}-->
                    """),
                'recommendation': '<!--{{ solution }}-->',
            },
        ),
    ])]

    def is_format(self, file):
        tree = parse_xml(file)
        report_format = tree.xpath('/report/report_format/name/text()')
        return report_format and report_format[0] == 'XML'

    def parse_openvas_findings(self, files):
        findings = []
        for file in files:
            for result_xml in parse_xml(file).xpath('//report/results/result'):
                finding = xml_to_dict(result_xml)

                # Parse nvt tags
                tags = finding.get("nvt", dict()).get("tags", "")
                tags = {i[0]: i[1] for i in (item.split("=", maxsplit=1) for item in tags.split("|"))}
                finding |= tags

                finding['oid'] = finding['nvt'].get('@oid')
                finding['title'] = finding['name']

                severity = finding.get('severities', {}).get('severity', {})
                if severity and isinstance(severity, list):
                    severity = severity[0]
                finding['cvss'] = cvss2_to_cvss31(severity.get('value'))
                finding['severity'] = cvss.level_from_score(float(finding.get('severity') or '0')).value

                host_xml = result_xml.find('host')
                finding['host'] = xml_to_dict(host_xml) | {
                    'ip': next(iter(result_xml.xpath('host/text()')), None),
                    'hostname': next(iter(result_xml.xpath('host/hostname/text()')), None),
                    'port': next(iter(result_xml.xpath('host/port/text()')), None),
                }
                finding['target'] = finding['host']['hostname'] or finding['host']['ip']
                finding['affected_components'] = [f"{finding['target']}{':' + finding['port'] if not finding['port'].startswith('general') else ''}"]
                finding['references'] = result_xml.xpath('nvt/refs/ref[@type="url"]/@id')

                findings.append(finding)

        findings = sorted(findings, key=lambda f: cvss.calculate_score(f['cvss']))
        return findings
    
    def merge_findings_by_plugin(self, findings):
        out = []
        for _, findings in groupby_to_dict(findings, key=lambda f: f['oid']).items():
            merged = findings[0]
            for f in findings[1:]:
                merged['affected_components'].extend(f['affected_components'])
                merged['references'] = list(set(merged['references'] + f['references']))
            out.append(merged)
        return out

    def parse_notes(self, files):
        notes = []

        note_root = ProjectNotebookPage(
            title='OpenVAS',
            icon_emoji='🦖',
        )
        notes.append(note_root)

        order = 0
        for target, findings in groupby_to_dict(self.parse_openvas_findings(files), key=lambda f: f['target']).items():
            order += 1
            note_host = ProjectNotebookPage(
                parent=note_root,
                order=order,
                checked=False,
                title=target,
                text=render_template_string(textwrap.dedent(
                    """\
                    **Target:** <!--{{ findings.0.target }}-->  
                    **IP:** <!--{{ findings.0.host.ip|default:"n/a" }}-->  

                    ## Vulnerability overview

                    | Title | Severity |
                    | ------- | ------- |
                    <!--{% for f in findings %}-->| <!--{{f.title}}--> | <!--{{f.severity}}--> |
                    <!--{% endfor %}-->

                    """), context={'findings': findings}))
            notes.append(note_host)
            for idx, finding in enumerate(self.merge_findings_by_plugin(findings)):
                notes.append(ProjectNotebookPage(
                    parent=note_host,
                    order=idx + 1,
                    checked=False,
                    title=f"{self.severity_mapping.get(finding['severity'])} {finding['title']}",
                    text=render_template_string(textwrap.dedent(
                        """\
                        **OID:** <!--{{ nvt.oid }}-->  
                        **Severity:** <!--{{ severity }}-->  
                        **Port:** <!--{{ port }}-->  

                        ## Description
                        <!--{{ summary }}-->

                        <!--{{ impact }}-->

                        ## Solution
                        <!--{{ solution }}-->
                        """), context=finding),
                ))

        return notes

    def parse_findings(self, files, project):
        findings = []
        templates = self.get_all_finding_templates()
        for issue in self.merge_findings_by_plugin(self.parse_openvas_findings(files)):
            findings.append(self.generate_finding_from_template(
                tr=self.select_finding_template(
                    templates=templates,
                    fallback=self.fallback_templates,
                    selector=issue.get('oid'),
                    language=project.language,
                ),
                data=issue,
                project=project,
            ))

        return findings

