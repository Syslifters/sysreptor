import json
import re
import textwrap

from sysreptor.pentests.models import (
    FindingTemplateTranslation,
    Language,
    ProjectNotebookPage,
)
from sysreptor.utils.utils import groupby_to_dict

from ..utils import render_template_string
from .base import BaseImporter, fallback_template

# ScoutSuite finding "level" -> SysReptor's 5-point severity scale.
# ScoutSuite has no notion of "critical" itself, so "danger" is mapped to
# "high" by default - bump specific checks up via a scanimport:scoutsuite:<finding_id>
# finding template if a particular check should always be critical for you.
LEVEL_TO_SEVERITY = {
    "danger": "high",
    "warning": "medium",
    "good_practice": "info",
    "info": "info",
}


class ScoutSuiteImporter(BaseImporter):
    id = 'scoutsuite'

    fallback_templates = [fallback_template(tags=[f'scanimport:{id}'], translations=[
        FindingTemplateTranslation(
            language=Language.ENGLISH_US,
            custom_fields={
                'summary': '<!--{{ rationale|default:description }}-->',
                'description': textwrap.dedent("""\
                    <!--{{ description }}-->

                    Affected resources (<!--{{ affected_components|length }}-->):
                    <!--{% for c in affected_components %}-->
                    - <!--{{ c }}-->
                    <!--{% endfor %}-->
                    """),
            },
        ),
    ])]

    def is_format(self, file):
        try:
            self._load_scoutsuite_json(file)
            return True
        except (json.JSONDecodeError, UnicodeDecodeError):
            return False

    def _load_scoutsuite_json(self, file):
        file.seek(0)
        raw = file.read().decode('utf-8', errors='strict').strip()

        # ScoutSuite's default report is a .js file containing a single
        # assignment: `scoutsuite_results = { ... };`. Strip that wrapper if
        # present so both the .js report and a plain .json export work.
        m = re.search(r"=\s*(\{.*\})\s*;?\s*$", raw, re.DOTALL)
        json_text = m.group(1) if m else raw

        data = json.loads(json_text)
        if not isinstance(data, dict) or 'services' not in data:
            raise json.JSONDecodeError("Not a ScoutSuite report (missing 'services' key)", json_text, 0)
        return data

    def parse_scoutsuite_findings(self, files):
        findings = []
        for file in files:
            results = self._load_scoutsuite_json(file)
            account = (
                results.get('account_id')
                or results.get('aws_account_id')
                or results.get('provider_name')
                or 'unknown'
            )
            services = results.get('services', {})
            for service_name, service_data in services.items():
                if not isinstance(service_data, dict):
                    continue
                for finding_id, finding in (service_data.get('findings') or {}).items():
                    if not isinstance(finding, dict):
                        continue

                    level = (finding.get('level') or 'warning').lower()
                    severity = LEVEL_TO_SEVERITY.get(level, 'medium')

                    items = finding.get('items') or []
                    if not isinstance(items, list):
                        items = [str(items)]

                    region = None
                    if items and isinstance(items[0], str):
                        parts = items[0].split('.')
                        if len(parts) > 1 and parts[0] == 'regions':
                            region = parts[1]

                    findings.append({
                        'finding_id': finding_id,
                        'title': (finding.get('description') or finding_id).strip(),
                        'severity': severity,
                        'service': service_name,
                        'region': region,
                        'account': account,
                        'description': (finding.get('description') or '').strip(),
                        'rationale': (finding.get('rationale') or '').strip(),
                        'references': list(finding.get('references') or []),
                        'affected_components': list(items),
                    })
        return findings

    def merge_findings_by_check(self, findings):
        """One finding per (service, finding_id) - matches how the Nessus
        importer merges by plugin ID, so the same check across many
        resources/accounts becomes a single finding rather than dozens of
        near-duplicates. Title, severity and references of a specific check
        can be customised via a scanimport:scoutsuite:<finding_id> finding
        template, the same way the other importers are customised."""
        out = []
        for _, group in groupby_to_dict(findings, key=lambda f: (f['service'], f['finding_id'])).items():
            merged = group[0]
            for f in group[1:]:
                merged['affected_components'] = list(dict.fromkeys(merged['affected_components'] + f['affected_components']))
                merged['references'] = list(dict.fromkeys(merged['references'] + f['references']))
            out.append(merged)
        return out

    def parse_notes(self, files):
        notes = []
        note_root = ProjectNotebookPage(title='ScoutSuite', icon_emoji='🔎')
        notes.append(note_root)

        findings = self.merge_findings_by_check(self.parse_scoutsuite_findings(files))
        order = 0
        for service, service_findings in groupby_to_dict(findings, key=lambda f: f['service']).items():
            order += 1
            notes.append(ProjectNotebookPage(
                parent=note_root,
                order=order,
                checked=False,
                title=service,
                text=render_template_string(textwrap.dedent("""\
                    | Finding | Severity | Resources |
                    | ------- | -------- | --------- |
                    <!--{% for f in findings %}-->| <!--{{ f.title }}--> | <!--{{ f.severity }}--> | <!--{{ f.affected_components|length }}--> |
                    <!--{% endfor %}-->
                    """), context={'findings': service_findings}),
            ))
        return notes

    def parse_findings(self, files, project):
        findings = []
        templates = self.get_all_finding_templates()
        for issue in self.merge_findings_by_check(self.parse_scoutsuite_findings(files)):
            findings.append(self.generate_finding_from_template(
                project=project,
                tr=self.select_finding_template(
                    templates=templates,
                    fallback=self.fallback_templates,
                    selector=issue.get('finding_id'),
                    language=project.language,
                ),
                data=issue,
            ))
        return findings
