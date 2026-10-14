import json
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from sysreptor.tests.mock import create_project, create_template, create_user

from ..importers import registry

DARKMOON_PATH = Path(__file__).parent / "data" / "darkmoon" / "darkmoon_findings.json"


@pytest.mark.django_db
class TestDarkmoonImporter:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.project = create_project(members=[create_user()])
        self.importer = registry.get('darkmoon')

    def test_is_format_object_with_findings(self):
        with DARKMOON_PATH.open('rb') as f:
            assert self.importer.is_format(f) is True

    def test_is_format_bare_list(self):
        findings = json.loads(DARKMOON_PATH.read_text())['findings']
        f = SimpleUploadedFile("findings.json", json.dumps(findings).encode())
        assert self.importer.is_format(f) is True

    def test_is_format_rejects_other_json(self):
        # Other JSON based reports must not be picked up by auto-detection.
        for content in [b'{"server_scan_results": []}', b'{"@programName": "OWASP ZAP"}', b'{"services": {}}', b'[{"title": "x", "severity": "high"}]', b'{"findings": []}']:
            assert self.importer.is_format(SimpleUploadedFile("other.json", content)) is False

    def test_is_format_rejects_non_json(self):
        assert self.importer.is_format(SimpleUploadedFile("data.txt", b"not json at all")) is False

    def test_auto_detection_selects_darkmoon(self):
        with DARKMOON_PATH.open('rb') as f:
            assert registry.auto_detect_format(f).id == 'darkmoon'

    def test_parse_findings_data(self):
        with DARKMOON_PATH.open('rb') as f:
            findings = self.importer.parse_darkmoon_findings([f])
        assert [f['severity'] for f in findings] == ['critical', 'high', 'medium']
        rce = findings[0]
        assert rce['title'] == 'Unauthenticated remote code execution in file upload handler'
        assert rce['status'] == 'exploited'
        assert rce['cvss'] == 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H'
        assert rce['cvss_score'] == 9.8
        assert rce['affected_components'] == ['https://app.example.test/upload']
        assert rce['references'] == [
            'https://nvd.nist.gov/vuln/detail/CVE-2026-12345',
            'https://attack.mitre.org/techniques/T1190/',
        ]
        assert len(rce['evidence_commands']) == 2
        assert rce['evidence_commands_text'].splitlines()[0].startswith('curl -s -F')

    def test_optional_fields_missing(self):
        ssrf = self.importer.parse_darkmoon_findings([DARKMOON_PATH.open('rb')])[2]
        assert ssrf['status'] == 'unconfirmed'
        assert ssrf['cvss'] is None
        assert ssrf['references'] == []
        assert ssrf['evidence_commands'] == []

    def test_mitre_subtechnique_reference(self):
        xss = self.importer.parse_darkmoon_findings([DARKMOON_PATH.open('rb')])[1]
        assert xss['references'] == ['https://attack.mitre.org/techniques/T1059/007/']

    def test_invalid_cvss_vector_ignored(self):
        data = {'findings': [{
            'title': 'x', 'severity': 'low', 'status': 'confirmed', 'discovered_by_agent': 'php', 'cvss_vector': 'not-a-vector',
        }]}
        f = SimpleUploadedFile("findings.json", json.dumps(data).encode())
        assert self.importer.parse_darkmoon_findings([f])[0]['cvss'] is None

    def test_parse_notes_structure(self):
        with DARKMOON_PATH.open('rb') as f:
            notes = self.importer.parse_notes([f])
        assert notes[0].title == 'Darkmoon'
        assert {n.title for n in notes[1:]} == {'app.example.test', 'api.example.test'}

    def test_parse_findings_creates_one_per_finding(self):
        with DARKMOON_PATH.open('rb') as f:
            findings = self.importer.parse_findings(files=[f], project=self.project)
        assert len(findings) == 3
        rce = findings[0]
        assert rce.data['title'] == 'Unauthenticated remote code execution in file upload handler'
        assert 'exploited' in rce.data['description']
        assert 'curl -s -F' in rce.data['description']

    def test_template_selected_by_category(self):
        t = create_template(tags=['scanimport:darkmoon:xss_stored'], data={'title': 'Stored XSS'})
        with DARKMOON_PATH.open('rb') as f:
            findings = self.importer.parse_findings(files=[f], project=self.project)
        xss = next(f for f in findings if f.template_info['search_path'][0] == 'scanimport:darkmoon:xss_stored')
        assert xss.template_id == t.id
        assert xss.data['title'] == 'Stored XSS'
