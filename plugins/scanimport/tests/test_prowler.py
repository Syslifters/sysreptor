from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from sysreptor.tests.mock import create_project, create_user

from ..importers import registry

PROWLER_DATA_DIR = Path(__file__).parent / "data" / "prowler"
PROWLER_V4_PATH = PROWLER_DATA_DIR / "prowler_v4.csv"
PROWLER_V3_PATH = PROWLER_DATA_DIR / "prowler_v3.csv"
PROWLER_OCSF_PATH = PROWLER_DATA_DIR / "prowler_ocsf.json"


@pytest.mark.django_db
class TestProwlerImporter:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.project = create_project(members=[create_user()])
        self.importer = registry.get('prowler')

    def test_is_format_comma_delimited(self):
        with PROWLER_V4_PATH.open('rb') as f:
            assert self.importer.is_format(f) is True

    def test_is_format_semicolon_delimited(self):
        with PROWLER_V3_PATH.open('rb') as f:
            assert self.importer.is_format(f) is True

    def test_is_format_rejects_non_prowler_csv(self):
        # A CSV without the required CHECK_ID/STATUS columns is not Prowler output.
        f = SimpleUploadedFile("other.csv", b"name,value\nfoo,bar\n")
        assert self.importer.is_format(f) is False

    def test_is_format_rejects_non_csv(self):
        f = SimpleUploadedFile("data.txt", b"just some plain text without columns")
        assert self.importer.is_format(f) is False

    def test_only_failed_checks_are_kept(self):
        # prowler_v4 has 3 FAIL rows (2 share a check), 1 PASS and 1 MANUAL.
        with PROWLER_V4_PATH.open('rb') as f:
            findings = self.importer.parse_prowler_findings([f])
        check_ids = {f['check_id'] for f in findings}
        assert 'ec2_ebs_volume_encryption' not in check_ids  # PASS dropped
        assert 'guardduty_is_enabled' not in check_ids        # MANUAL dropped
        assert check_ids == {'s3_bucket_public_access', 'iam_password_policy_minimum_length_14'}

    def test_merge_combines_resources_per_check(self):
        with PROWLER_V4_PATH.open('rb') as f:
            merged = self.importer.merge_findings_by_check(self.importer.parse_prowler_findings([f]))
        by_check = {f['check_id']: f for f in merged}
        assert len(merged) == 2
        # The two FAIL rows for the same check collapse into one finding with both resources.
        assert sorted(by_check['s3_bucket_public_access']['affected_components']) == [
            'arn:aws:s3:::bucket-one', 'arn:aws:s3:::bucket-two',
        ]

    def test_severity_mapping(self):
        with PROWLER_V4_PATH.open('rb') as f:
            merged = self.importer.merge_findings_by_check(self.importer.parse_prowler_findings([f]))
        by_check = {f['check_id']: f for f in merged}
        assert by_check['s3_bucket_public_access']['severity'] == 'high'
        assert by_check['iam_password_policy_minimum_length_14']['severity'] == 'medium'

    def test_semicolon_delimiter_and_lowercase_aliases(self):
        # prowler_v3 is ';'-delimited with lowercase headers - exercises both
        # the delimiter sniffing and the column-alias resolution.
        with PROWLER_V3_PATH.open('rb') as f:
            merged = self.importer.merge_findings_by_check(self.importer.parse_prowler_findings([f]))
        by_check = {f['check_id']: f for f in merged}
        assert set(by_check) == {'rds_instance_backup_enabled', 'cloudtrail_multi_region_enabled'}
        assert by_check['rds_instance_backup_enabled']['title'] == 'RDS instance has backups enabled'
        assert by_check['rds_instance_backup_enabled']['service'] == 'rds'

    def test_parse_notes_structure(self):
        with PROWLER_V4_PATH.open('rb') as f:
            notes = self.importer.parse_notes([f])
        assert notes[0].title == 'Prowler'
        assert notes[0].icon_emoji == '☁️'
        # One child note per affected service.
        service_titles = {n.title for n in notes[1:]}
        assert {'s3', 'iam'} <= service_titles

    def test_parse_findings_uses_fallback_template(self):
        with PROWLER_V4_PATH.open('rb') as f:
            findings = self.importer.parse_findings(files=[f], project=self.project)
        assert len(findings) == 2
        assert all(getattr(f, 'template_info', {}).get('is_fallback') for f in findings)


@pytest.mark.django_db
class TestProwlerOcsfImporter:
    """Prowler v4/v5 also emit JSON-OCSF; the same importer detects and parses it."""

    @pytest.fixture(autouse=True)
    def setUp(self):
        self.project = create_project(members=[create_user()])
        self.importer = registry.get('prowler')

    def test_is_format_detects_ocsf_json(self):
        with PROWLER_OCSF_PATH.open('rb') as f:
            assert self.importer.is_format(f) is True

    def test_is_format_rejects_non_prowler_json(self):
        # A JSON document without metadata.event_code is not Prowler OCSF output
        # (e.g. a ScoutSuite report keyed by "services").
        f = SimpleUploadedFile("other.json", b'{"services": {"s3": {}}}')
        assert self.importer.is_format(f) is False

    def test_only_failed_checks_are_kept(self):
        # The fixture has 3 FAIL findings (2 share a check), 1 PASS and 1 MANUAL.
        with PROWLER_OCSF_PATH.open('rb') as f:
            findings = self.importer.parse_prowler_findings([f])
        check_ids = {f['check_id'] for f in findings}
        assert 'ec2_ebs_volume_encryption' not in check_ids  # PASS dropped
        assert 'guardduty_is_enabled' not in check_ids        # MANUAL dropped
        assert check_ids == {'s3_bucket_public_access', 'iam_password_policy_minimum_length_14'}

    def test_merge_combines_resources_per_check(self):
        with PROWLER_OCSF_PATH.open('rb') as f:
            merged = self.importer.merge_findings_by_check(self.importer.parse_prowler_findings([f]))
        by_check = {f['check_id']: f for f in merged}
        assert len(merged) == 2
        assert sorted(by_check['s3_bucket_public_access']['affected_components']) == [
            'arn:aws:s3:::bucket-one', 'arn:aws:s3:::bucket-two',
        ]

    def test_field_and_severity_mapping(self):
        with PROWLER_OCSF_PATH.open('rb') as f:
            merged = self.importer.merge_findings_by_check(self.importer.parse_prowler_findings([f]))
        s3 = next(f for f in merged if f['check_id'] == 's3_bucket_public_access')
        assert s3['severity'] == 'high'
        assert s3['title'] == 'S3 Bucket has public access configured'
        assert s3['service'] == 's3'
        assert s3['account'] == '123456789012'
        # Remediation references from OCSF flow through (the CSV export has none).
        assert any('block-public-access' in r for r in s3['references'])

    def test_parse_findings_uses_fallback_template(self):
        with PROWLER_OCSF_PATH.open('rb') as f:
            findings = self.importer.parse_findings(files=[f], project=self.project)
        assert len(findings) == 2
        assert all(getattr(f, 'template_info', {}).get('is_fallback') for f in findings)
