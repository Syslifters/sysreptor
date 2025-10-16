import re
import textwrap
from base64 import b64decode

from sysreptor.pentests.models import (
    FindingTemplateTranslation,
    Language,
    ProjectNotebookPage,
)
from sysreptor.utils.utils import groupby_to_dict

from ..utils import html_to_markdown, parse_xml, render_template_string, xml_to_dict
from .base import BaseImporter, fallback_template


def to_inline_code(tag, text, **kwargs):
    return f'`{text}`'


class BurpImporter(BaseImporter):
    id = 'burp'

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
        version = tree.xpath('/issues/@burpVersion')
        return bool(version)
    
    def parse_burp_issues(self, files):
        issues = []
        for file in files:
            for tree in parse_xml(file).xpath('/issues/issue'):
                issue = xml_to_dict(
                    node=tree,
                    elements_str=['type', 'name', 'severity', 'references', 'issueBackground', 'issueDetail', 'remediationDetail', 'remediationBackground', 'host', 'path', 'location', 'confidence', 'vulnerabilityClassifications'],
                ) | {
                    'issueDetailItems': tree.xpath('issueDetailItems/issueDetailItem/text()'),
                    'requestresponse': [{
                        'request': b64decode(rr.findtext('request[@base64="true"]') or ''),
                        'response': b64decode(rr.findtext('response[@base64="true"]') or ''),
                    } for rr in tree.xpath('requestresponse')]
                }

                # Exclude false positives
                if issue.get('severity') == 'False Positive':
                    continue

                # Normalize severity
                issue['severity'] = issue.get('severity', 'info').lower()
                if issue['severity'] == 'information':
                    issue['severity'] = 'info'
                issue["severity_score"] = list(self.severity_mapping.keys()).index(issue["severity"]) + 1

                # References to list
                issue['references'] = re.findall(r"<a\s+href=['\"](.*?)['\"]", issue.get('references') or "")

                # Affected components
                issue['affected_components'] = []
                issue['ip'] = None
                if (host := tree.find('host')) is not None:
                    issue['ip'] = host.attrib.get("@ip")
                    url = issue.get('host') or issue['ip']
                    location = issue.get("location") or issue.get("path") or ''
                    issue['affected_components'].append(f"{url}{location}{f' ({issue['ip']})' if issue['ip'] and url else ''}")
                
                # Post process fields
                issue['title'] = issue.pop('name', '')
                for k in ['issueBackground', 'issueDetail', 'remediationBackground']:
                    if v := issue.get(k):
                        issue[k] = html_to_markdown(v, map_tags={'b': 'code', 'i': 'code'})

                issues.append(issue)

        # Order by severity
        issues = sorted(issues, key=lambda x: (x.get("severity_score", 0) * -1, x.get('title', '')))
        return issues
    
    def group_issues_by_ip(self, issues) -> dict:
        out = {}
        for ip, findings in groupby_to_dict(issues, key=lambda i: i.get('ip') or i.get('host') or '_').items():
            if ip != "_":
                out[ip] = self.merge_findings_by_type(findings)
            else:
                out[ip] = findings
        return out
    
    def merge_findings_by_type(self, issues: list[dict]) -> list:
        out = []
        for type, issues in groupby_to_dict(issues, key=lambda x: x.get('type', '')).items():
            if not type:
                # No type to group by
                out.extend(issues)
            else:
                # Merge affected components
                merged = issues[0]
                for i in issues[1:]:
                    merged['affected_components'].extend(i['affected_components'])
                out.append(merged)

        out = sorted(out, key=lambda x: (x.get("severity_score", 0) * -1, x.get('type'), x.get('title', '')))
        return out

    def parse_notes(self, files):
        notes = []

        # Main note
        note_root = ProjectNotebookPage(
            icon_emoji='🟧',
            title='Burp',
            text=''
        )
        notes.append(note_root)

        order = 0
        for ip, issues in self.group_issues_by_ip(self.parse_burp_issues(files)).items():
            order += 1
            note_ip = ProjectNotebookPage(
                parent=note_root,
                order=order,
                checked=False,
                title=ip,
                text=render_template_string(textwrap.dedent(
                    """\
                    # Burp Scan

                    **Target:** <!--{{ ip }}-->  

                    ## Vulnerability overview

                    | Title | Severity | Affected Components |
                    | ------- | ------- | ------- |
                    <!--{% for f in findings %}--><!--{% oneliner %}-->
                    | <!--{{f.title}}-->
                    | <!--{{f.severity|title}}-->
                    | <!--{% if f.affected_components|length > 0 %}--><ul>
                    <!--{% for a in f.affected_components %}--><li><!--{{a}}--></li><!--{% endfor %}-->
                    </ul><!--{% endif %}--> |
                    <!--{% endoneliner %}-->
                    <!--{% endfor %}-->
                    """), { 'ip': ip, 'findings': issues }),
            )
            notes.append(note_ip)
            for idx, issue in enumerate(self.merge_findings_by_type(issues)):
                notes.append(ProjectNotebookPage(
                    parent=note_ip,
                    order=idx + 1,
                    checked=False,
                    title=f"{self.severity_mapping.get(issue.get('severity', 'info').lower())} {issue.get('title', '')}",
                    text=render_template_string(textwrap.dedent(
                        """\
                        **Type (plugin ID):** <!--{{ type }}-->  
                        **Severity:** <!--{{ severity|title }}-->  

                        <!--{{ issueDetail }}-->

                        <!--{% if affected_components|length > 0 %}-->## Affected Components
                        <!--{% for a in affected_components %}-->* <!--{{ a }}-->
                        <!--{% endfor %}--><!--{% endif %}-->

                        ## Detail
                        <!--{{  issueBackground }}-->

                        ## Remediation
                        <!--{{ remediationBackground }}-->

                        <!--{% if references|length > 0 %}-->## References
                        <!--{% for r in references %}-->* <!--{{ r }}--> 
                        <!--{% endfor %}--><!--{% endif %}-->
                        """), issue),
                ))

        if len(notes) == 1:
            # Only root note: nothing to add
            return []
        return notes

    def parse_findings(self, files, project):
        findings = []
        templates = self.get_all_finding_templates()
        for issue in self.merge_findings_by_type(self.parse_burp_issues(files)):
            findings.append(self.generate_finding_from_template(
                tr=self.select_finding_template(
                    templates=templates,
                    fallback=self.fallback_templates,
                    selector=issue.get('type'),
                    language=project.language,
                ),
                data=issue,
                project=project,
            ))

        return findings

