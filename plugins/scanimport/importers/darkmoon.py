import json
import textwrap
from urllib.parse import urlparse

from sysreptor.pentests import cvss
from sysreptor.pentests.models import (
    FindingTemplateTranslation,
    Language,
    ProjectNotebookPage,
)
from sysreptor.utils.utils import groupby_to_dict

from ..utils import render_template_string
from .base import BaseImporter, fallback_template

# Darkmoon severities -> SysReptor's 5-point severity scale.
SEVERITY_MAPPING = {
    "critical": "critical",
    "high": "high",
    "medium": "medium",
    "low": "low",
    "informational": "info",
    "info": "info",
}
SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]

# Darkmoon proves findings with a real exploit attempt and labels the outcome.
EXPLOITATION_STATUSES = {"exploited", "confirmed", "unconfirmed"}


class DarkmoonImporter(BaseImporter):
    """
    Importer for the JSON findings produced by Darkmoon, an open source (GPL-3.0)
    autonomous AI penetration testing platform (https://github.com/ASCIT31/Dark-Moon).

    Accepts either a bare list of findings or an object with a top-level
    "findings" list. Each finding uses the Darkmoon finding schema
    (title, severity, cvss_score, category, status, description, endpoint,
    discovered_by_agent and the optional remediation, cve, cvss_vector,
    mitre_attack_id, evidence_*, raw_request, raw_response, ...).
    """
    id = 'darkmoon'

    fallback_templates = [fallback_template(tags=[f'scanimport:{id}'], translations=[
        FindingTemplateTranslation(
            language=Language.ENGLISH_US,
            custom_fields={
                'summary': '<!--{{ description }}-->',
                'description': textwrap.dedent("""\
                    **Exploitation status:** <!--{{ status }}-->

                    <!--{% if evidence_explanation %}-->
                    <!--{{ evidence_explanation }}-->
                    <!--{% endif %}-->

                    <!--{% if evidence_commands_text %}-->
                    Commands used to prove the finding:

                    ```
                    <!--{{ evidence_commands_text }}-->
                    ```
                    <!--{% endif %}-->

                    <!--{% if evidence_logs %}-->
                    ```
                    <!--{{ evidence_logs }}-->
                    ```
                    <!--{% endif %}-->

                    <!--{% if raw_request %}-->
                    Request:

                    ```http
                    <!--{{ raw_request }}-->
                    ```
                    <!--{% endif %}-->

                    <!--{% if raw_response %}-->
                    Response:

                    ```http
                    <!--{{ raw_response }}-->
                    ```
                    <!--{% endif %}-->
                    """),
                'recommendation': '<!--{{ remediation }}-->',
            },
        ),
    ])]

    @staticmethod
    def _load_findings(file):
        file.seek(0)
        data = json.loads(file.read().decode('utf-8', errors='strict'))
        if isinstance(data, dict):
            data = data.get('findings')
        if not isinstance(data, list):
            raise ValueError("Not a Darkmoon findings report")
        return [f for f in data if isinstance(f, dict)]

    @staticmethod
    def _is_darkmoon_finding(finding):
        # Fields of the Darkmoon finding schema that no other supported
        # importer produces: the discovering agent and the exploitation status.
        return bool(
            finding.get('title')
            and finding.get('discovered_by_agent')
            and str(finding.get('status', '')).lower() in EXPLOITATION_STATUSES
        )

    def is_format(self, file):
        try:
            findings = self._load_findings(file)
        except (ValueError, UnicodeDecodeError):
            return False
        return bool(findings) and all(self._is_darkmoon_finding(f) for f in findings)

    def parse_darkmoon_findings(self, files):
        findings = []
        for file in files:
            for item in self._load_findings(file):
                severity = SEVERITY_MAPPING.get(str(item.get('severity') or '').lower(), 'info')

                vector = (item.get('cvss_vector') or '').strip() or None
                if vector and not (cvss.is_cvss(vector) and not cvss.is_cvss2(vector)):
                    vector = None

                try:
                    cvss_score = float(item.get('cvss_score'))
                except (TypeError, ValueError):
                    cvss_score = None

                commands = item.get('evidence_commands') or []
                if isinstance(commands, str):
                    commands = [commands]

                references = []
                cve = (item.get('cve') or '').strip().upper() or None
                if cve:
                    references.append(f'https://nvd.nist.gov/vuln/detail/{cve}')
                mitre_id = (item.get('mitre_attack_id') or '').strip() or None
                if mitre_id:
                    references.append(f"https://attack.mitre.org/techniques/{mitre_id.replace('.', '/')}/")

                endpoint = item.get('endpoint')
                findings.append({
                    'title': item['title'].strip(),
                    'severity': severity,
                    'cvss': vector,
                    'cvss_score': cvss_score,
                    'status': str(item.get('status') or '').lower(),
                    'category': item.get('category'),
                    'agent': item.get('discovered_by_agent'),
                    'component': item.get('plugin_or_component'),
                    'node_id': item.get('node_id'),
                    'cve': cve,
                    'mitre_attack_id': mitre_id,
                    'mitre_attack_name': item.get('mitre_attack_name'),
                    'iso27001_control': item.get('iso27001_control'),
                    'description': (item.get('description') or '').strip(),
                    'remediation': (item.get('remediation') or '').strip(),
                    'evidence_explanation': (item.get('evidence_explanation') or '').strip(),
                    'evidence_commands': [str(c) for c in commands],
                    'evidence_commands_text': '\n'.join(str(c) for c in commands),
                    'evidence_logs': item.get('evidence_logs'),
                    'raw_request': item.get('raw_request'),
                    'raw_response': item.get('raw_response'),
                    'recommendation': (item.get('remediation') or '').strip(),
                    'references': references,
                    'affected_components': [endpoint] if endpoint else [],
                    'host': (urlparse(endpoint).netloc if endpoint else '') or 'n/a',
                })

        # Most severe first: by CVSS score when known, otherwise by severity bucket.
        return sorted(findings, key=lambda f: (
            SEVERITY_ORDER.index(f['severity']),
            -(f['cvss_score'] or 0),
        ))

    def parse_notes(self, files):
        notes = []
        note_root = ProjectNotebookPage(title='Darkmoon', icon_emoji='🌑')
        notes.append(note_root)

        findings = self.parse_darkmoon_findings(files)
        order = 0
        for host, host_findings in groupby_to_dict(findings, key=lambda f: f['host'] or 'n/a').items():
            order += 1
            notes.append(ProjectNotebookPage(
                parent=note_root,
                order=order,
                checked=False,
                title=host,
                text=render_template_string(textwrap.dedent("""\
                    | Finding | Severity | Status | Endpoint |
                    | ------- | -------- | ------ | -------- |
                    <!--{% for f in findings %}-->| <!--{{ f.title }}--> | <!--{{ f.severity }}--> | <!--{{ f.status }}--> | <!--{% for c in f.affected_components %}--><!--{{ c }}--><!--{% endfor %}--> |
                    <!--{% endfor %}-->
                    """), context={'findings': host_findings}),
            ))
        return notes

    def parse_findings(self, files, project):
        findings = []
        templates = self.get_all_finding_templates()
        for issue in self.parse_darkmoon_findings(files):
            findings.append(self.generate_finding_from_template(
                project=project,
                tr=self.select_finding_template(
                    templates=templates,
                    fallback=self.fallback_templates,
                    selector=issue.get('category'),
                    language=project.language,
                ),
                data=issue,
            ))
        return findings
