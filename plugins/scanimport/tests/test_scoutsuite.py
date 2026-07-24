from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from sysreptor.tests.mock import create_project, create_user

from ..importers import registry

SCOUTSUITE_DATA_DIR = Path(__file__).parent / "data" / "scoutsuite"
SCOUTSUITE_JS_PATH = SCOUTSUITE_DATA_DIR / "scoutsuite_results.js"
SCOUTSUITE_JSON_PATH = SCOUTSUITE_DATA_DIR / "scoutsuite_results.json"


@pytest.mark.django_db
class TestScoutSuiteImporter:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.project = create_project(members=[create_user()])
        self.importer = registry.get('scoutsuite')

    def test_is_format_js_wrapper(self):
        # The default ScoutSuite report is a .js file: `scoutsuite_results = {...};`
        with SCOUTSUITE_JS_PATH.open('rb') as f:
            assert self.importer.is_format(f) is True

    def test_is_format_plain_json(self):
        with SCOUTSUITE_JSON_PATH.open('rb') as f:
            assert self.importer.is_format(f) is True

    def test_is_format_rejects_json_without_services(self):
        # A JSON document without a top-level "services" key is not ScoutSuite output
        # (guards against grabbing e.g. SSLyze/ZAP JSON reports).
        f = SimpleUploadedFile("other.json", b'{"server_scan_results": []}')
        assert self.importer.is_format(f) is False

    def test_is_format_rejects_non_json(self):
        f = SimpleUploadedFile("data.txt", b"not json at all")
        assert self.importer.is_format(f) is False

    def test_level_maps_to_severity(self):
        with SCOUTSUITE_JS_PATH.open('rb') as f:
            findings = self.importer.parse_scoutsuite_findings([f])
        by_id = {f['finding_id']: f for f in findings}
        assert by_id['s3-bucket-allowing-cleartext']['severity'] == 'high'      # danger
        assert by_id['s3-bucket-versioning-disabled']['severity'] == 'medium'   # warning
        assert by_id['iam-password-policy-expiration']['severity'] == 'info'    # good_practice

    def test_merge_combines_items_per_check(self):
        with SCOUTSUITE_JS_PATH.open('rb') as f:
            merged = self.importer.merge_findings_by_check(self.importer.parse_scoutsuite_findings([f]))
        by_id = {f['finding_id']: f for f in merged}
        assert by_id['s3-bucket-allowing-cleartext']['affected_components'] == [
            'regions.eu-west-1.buckets.bucket-one',
            'regions.eu-west-1.buckets.bucket-two',
        ]

    def test_metadata_extracted(self):
        with SCOUTSUITE_JS_PATH.open('rb') as f:
            findings = self.importer.parse_scoutsuite_findings([f])
        by_id = {f['finding_id']: f for f in findings}
        s3 = by_id['s3-bucket-allowing-cleartext']
        assert s3['service'] == 's3'
        assert s3['account'] == '123456789012'
        assert s3['region'] == 'eu-west-1'
        assert s3['references'] == ['https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html']

    def test_parse_notes_structure(self):
        with SCOUTSUITE_JS_PATH.open('rb') as f:
            notes = self.importer.parse_notes([f])
        assert notes[0].title == 'ScoutSuite'
        assert notes[0].icon_emoji == '🔎'
        service_titles = {n.title for n in notes[1:]}
        assert {'s3', 'iam'} <= service_titles

    def test_parse_findings_creates_one_per_check(self):
        with SCOUTSUITE_JS_PATH.open('rb') as f:
            findings = self.importer.parse_findings(files=[f], project=self.project)
        assert len(findings) == 3
