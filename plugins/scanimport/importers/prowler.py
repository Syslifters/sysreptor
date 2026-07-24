import csv
import io
import json
import textwrap

from sysreptor.pentests.models import (
    FindingTemplateTranslation,
    Language,
    ProjectNotebookPage,
)
from sysreptor.utils.utils import groupby_to_dict

from ..utils import render_template_string
from .base import BaseImporter, fallback_template

# Prowler's own severity scale maps almost 1:1 onto SysReptor's, aside from
# spelling out "informational" in full.
SEVERITY_MAPPING = {
    "critical": "critical",
    "high": "high",
    "medium": "medium",
    "low": "low",
    "informational": "info",
    "info": "info",
}

# OCSF severity_id -> SysReptor severity, used as a fallback when the textual
# `severity` field is absent. (OCSF: 1=Informational .. 5=Critical, 6=Fatal.)
OCSF_SEVERITY_ID_MAPPING = {1: "info", 2: "low", 3: "medium", 4: "high", 5: "critical", 6: "critical"}

# Column names have varied a little across Prowler v3/v4 CSV exports -
# list the aliases we know about so this keeps working across versions.
COLUMN_ALIASES = {
    "check_id": ["CHECK_ID", "CheckID", "check_id"],
    "title": ["CHECK_TITLE", "Title", "check_title"],
    "severity": ["SEVERITY", "Severity", "severity"],
    "status": ["STATUS", "Status", "status"],
    "status_extended": ["STATUS_EXTENDED", "StatusExtended", "status_extended"],
    "service": ["SERVICE_NAME", "ServiceName", "service_name"],
    "resource": ["RESOURCE_UID", "RESOURCE_TYPE", "ResourceId", "resource_uid"],
    "region": ["REGION", "Region", "region"],
    "account": ["ACCOUNT_ID", "AccountId", "account_id"],
}

REQUIRED_FOR_DETECTION = {"check_id", "status"}


def _resolve_columns(fieldnames):
    fieldnames = fieldnames or []
    return {key: next((a for a in aliases if a in fieldnames), None) for key, aliases in COLUMN_ALIASES.items()}


def _sniff_dialect(sample):
    try:
        return csv.Sniffer().sniff(sample, delimiters=";,")
    except csv.Error:
        return csv.excel


class ProwlerImporter(BaseImporter):
    id = 'prowler'

    fallback_templates = [fallback_template(tags=[f'scanimport:{id}'], translations=[
        FindingTemplateTranslation(
            language=Language.ENGLISH_US,
            custom_fields={
                'summary': '<!--{{ status_extended|default:title }}-->',
                'description': textwrap.dedent("""\
                    <!--{{ status_extended }}-->

                    Affected resources (<!--{{ affected_components|length }}-->):
                    <!--{% for c in affected_components %}-->
                    - <!--{{ c }}-->
                    <!--{% endfor %}-->
                    """),
            },
        ),
    ])]

    # ---- format handling -------------------------------------------------
    # Prowler v5 emits both CSV and JSON-OCSF by default; we accept either.
    # Both are normalised to the same finding dict shape so the merge, notes
    # and findings pipeline below is format-agnostic.

    def _read_text(self, file):
        file.seek(0)
        return file.read().decode('utf-8', errors='replace')

    @staticmethod
    def _looks_like_json(text):
        return text.lstrip()[:1] in ('[', '{')

    def is_format(self, file):
        try:
            text = self._read_text(file)
        except Exception:
            return False
        return self._is_ocsf(text) if self._looks_like_json(text) else self._is_csv(text)

    # ---- CSV -------------------------------------------------------------

    def _read_rows(self, text):
        dialect = _sniff_dialect(text[:4096])
        reader = csv.DictReader(io.StringIO(text), dialect=dialect)
        return reader.fieldnames or [], list(reader)

    def _is_csv(self, text):
        try:
            fieldnames, _ = self._read_rows(text)
        except Exception:
            return False
        col = _resolve_columns(fieldnames)
        return all(col[key] for key in REQUIRED_FOR_DETECTION)

    def _parse_csv(self, text):
        fieldnames, rows = self._read_rows(text)
        col = _resolve_columns(fieldnames)
        if not col["check_id"]:
            return []

        findings = []
        for row in rows:
            status = (row.get(col["status"], "") or "").strip().upper() if col["status"] else "FAIL"
            if status != "FAIL":
                # Drop PASS/MANUAL/NOT_APPLICABLE rows - this is the "minimise
                # the noise" step: Prowler emits one row per check per
                # resource, and only FAILs are actual findings.
                continue

            severity_raw = (row.get(col["severity"], "") or "info").strip().lower() if col["severity"] else "info"
            resource = (row.get(col["resource"], "") or "").strip() if col["resource"] else ""

            findings.append({
                "check_id": (row.get(col["check_id"], "") or "").strip(),
                "title": (row.get(col["title"], "") or "").strip() if col["title"] else "",
                "severity": SEVERITY_MAPPING.get(severity_raw, "info"),
                "status_extended": (row.get(col["status_extended"], "") or "").strip() if col["status_extended"] else "",
                "service": (row.get(col["service"], "") or "").strip() if col["service"] else "",
                "region": (row.get(col["region"], "") or "").strip() if col["region"] else "",
                "account": (row.get(col["account"], "") or "").strip() if col["account"] else "",
                "affected_components": [resource] if resource else [],
                "references": [],
            })
        return findings

    # ---- JSON-OCSF -------------------------------------------------------

    @staticmethod
    def _load_ocsf(text):
        data = json.loads(text)
        # Prowler emits a JSON array of OCSF detection findings; tolerate a
        # single object too.
        return [data] if isinstance(data, dict) else data

    def _is_ocsf(self, text):
        try:
            data = self._load_ocsf(text)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return False
        if not isinstance(data, list):
            return False
        first = next((f for f in data if isinstance(f, dict)), None)
        if not first:
            return False
        # The Prowler check id lives in metadata.event_code (with unmapped.check_id
        # as an older fallback); paired with a status field this is enough to
        # distinguish Prowler OCSF from other JSON reports (ScoutSuite, SSLyze, ZAP).
        metadata = first.get('metadata') or {}
        unmapped = first.get('unmapped') or {}
        has_check = bool(metadata.get('event_code') or unmapped.get('check_id'))
        has_status = ('status_code' in first) or ('status' in first)
        return has_check and has_status

    def _parse_ocsf(self, text):
        try:
            data = self._load_ocsf(text)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return []

        findings = []
        for fo in data:
            if not isinstance(fo, dict):
                continue
            status = str(fo.get('status_code') or fo.get('status') or 'FAIL').strip().upper()
            if status != 'FAIL':
                continue

            metadata = fo.get('metadata') or {}
            unmapped = fo.get('unmapped') or {}
            finding_info = fo.get('finding_info') or {}
            cloud = fo.get('cloud') or {}
            remediation = fo.get('remediation') or {}

            check_id = (metadata.get('event_code') or unmapped.get('check_id') or '').strip()

            severity = fo.get('severity')
            if severity:
                severity = SEVERITY_MAPPING.get(str(severity).strip().lower(), 'info')
            else:
                severity = OCSF_SEVERITY_ID_MAPPING.get(fo.get('severity_id'), 'info')

            components, service, region = [], '', ''
            for r in (fo.get('resources') or []):
                if not isinstance(r, dict):
                    continue
                uid = (r.get('uid') or r.get('name') or '').strip()
                if uid:
                    components.append(uid)
                if not service:
                    group = r.get('group') or {}
                    service = (group.get('name') if isinstance(group, dict) else '') or ''
                if not region:
                    region = (r.get('region') or '').strip()
            service = service or (unmapped.get('service_name') or '').strip()
            region = region or (cloud.get('region') or '').strip()

            account = cloud.get('account') or {}
            account = (account.get('uid') if isinstance(account, dict) else '') or (fo.get('account_uid') or '')

            references = remediation.get('references') or []
            if not isinstance(references, list):
                references = []

            findings.append({
                "check_id": check_id,
                "title": (finding_info.get('title') or check_id).strip(),
                "severity": severity,
                "status_extended": (fo.get('status_detail') or '').strip(),
                "service": service,
                "region": region,
                "account": account.strip(),
                "affected_components": list(dict.fromkeys(components)),
                "references": list(references),
            })
        return findings

    # ---- shared pipeline -------------------------------------------------

    def parse_prowler_findings(self, files):
        findings = []
        for file in files:
            text = self._read_text(file)
            findings.extend(self._parse_ocsf(text) if self._looks_like_json(text) else self._parse_csv(text))
        return findings

    def merge_findings_by_check(self, findings):
        """One finding per CHECK_ID, with every failing resource listed as an
        affected component - mirrors how the Nessus importer merges by
        plugin ID, and is what turns "50 rows, one per resource" into a
        single, sensible finding. Title, severity and references of a specific
        check can be customised via a scanimport:prowler:<check_id> finding
        template, the same way the other importers are customised."""
        out = []
        for _, group in groupby_to_dict(findings, key=lambda f: f['check_id']).items():
            merged = dict(group[0])
            merged['affected_components'] = list(merged['affected_components'])
            merged['references'] = list(merged.get('references') or [])
            for f in group[1:]:
                merged['affected_components'] = list(dict.fromkeys(merged['affected_components'] + f['affected_components']))
                merged['references'] = list(dict.fromkeys(merged['references'] + (f.get('references') or [])))
            out.append(merged)
        return out

    def parse_notes(self, files):
        notes = []
        note_root = ProjectNotebookPage(title='Prowler', icon_emoji='☁️')
        notes.append(note_root)

        findings = self.merge_findings_by_check(self.parse_prowler_findings(files))
        order = 0
        for service, service_findings in groupby_to_dict(findings, key=lambda f: f['service'] or 'other').items():
            order += 1
            notes.append(ProjectNotebookPage(
                parent=note_root,
                order=order,
                checked=False,
                title=service,
                text=render_template_string(textwrap.dedent("""\
                    | Check | Severity | Resources |
                    | ------- | -------- | --------- |
                    <!--{% for f in findings %}-->| <!--{{ f.title }}--> | <!--{{ f.severity }}--> | <!--{{ f.affected_components|length }}--> |
                    <!--{% endfor %}-->
                    """), context={'findings': service_findings}),
            ))
        return notes

    def parse_findings(self, files, project):
        findings = []
        templates = self.get_all_finding_templates()
        for issue in self.merge_findings_by_check(self.parse_prowler_findings(files)):
            findings.append(self.generate_finding_from_template(
                project=project,
                tr=self.select_finding_template(
                    templates=templates,
                    fallback=self.fallback_templates,
                    selector=issue.get('check_id'),
                    language=project.language,
                ),
                data=issue,
            ))
        return findings
