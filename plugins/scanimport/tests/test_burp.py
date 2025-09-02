from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from sysreptor.tests.mock import create_project, create_user

from ..importers import registry

BURP_XML_PATH = Path(__file__).parent / "data" / "burp" / "burp.xml"


@pytest.mark.django_db
class TestBurpImporter:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.project = create_project(members=[create_user()])
        self.importer = registry.get('burp')

    def test_is_format_valid_burp_file(self):
        with BURP_XML_PATH.open('rb') as f:
            assert self.importer.is_format(f) is True
        
    def test_is_format_invalid_file(self):
        invalid_xml = SimpleUploadedFile("invalid.xml", b"<root><invalid></invalid></root>")
        assert self.importer.is_format(invalid_xml) is False

    def test_parse_burp_issues_basic(self):
        with BURP_XML_PATH.open('rb') as f:
            issues = self.importer.parse_burp_issues([SimpleUploadedFile("burp.xml", f.read())])

        assert len(issues) > 0
        for issue in issues:
            assert {'title', 'severity', 'severity_score', 'affected_components', 'references'} - set(issue.keys()) == set([])
            assert issue['severity'] in ['info', 'low', 'medium', 'high', 'critical']
            assert issue['severity_score'] >= 1
            assert isinstance(issue['affected_components'], list)

    def test_parse_burp_issues_false_positive_exclusion(self):
        issues = self.importer.parse_burp_issues([SimpleUploadedFile("test.xml", b"""
            <?xml version="1.0"?>
            <issues burpVersion="2023.7.1">
                <issue>
                    <name>Test</name>
                    <severity>False Positive</severity>
                    <host>https://example.com</host>
                    <type>123456</type>
                </issue>
            </issues>
            """)])
        assert len(issues) == 0

    def test_parse_burp_issues_host_and_ip_handling(self):
        """Test proper handling of host and IP information"""
        with BURP_XML_PATH.open('rb') as f:
            issues = self.importer.parse_burp_issues([f])
        
        for issue in issues:
            for component in issue.get('affected_components', []):
                assert isinstance(component, str) and len(component) > 0

    def test_html_to_markdown_conversion(self):
        issue = self.importer.parse_burp_issues([SimpleUploadedFile("test.xml", b"""
        <?xml version="1.0"?>
        <issues burpVersion="2023.7.1">
            <issue>
                <name>Test</name>
                <severity>Low</severity>
                <host ip="192.168.1.1">https://example.com</host>
                <location>/test/path</location>
                <type>123456</type>
                <issueBackground><![CDATA[<p>This is <b>bold</b>\t          and <i>italic</i> text.</p>]]></issueBackground>
                <issueDetail><![CDATA[<ul><li>Item 1</li><li>Item 2</li></ul>]]></issueDetail>
                <references><![CDATA[<ul><li><a href="https://example.com/ref1">Reference 1</a></li><li><a href="https://example.com/ref2">Reference 2</a></li></ul>]]></references>
            </issue>
        </issues>
        """)])[0]
        assert issue['issueBackground'] == 'This is `bold` and `italic` text.\n\n'
        assert issue['issueDetail'] == '* Item 1\n* Item 2\n'
        assert issue['affected_components'] == ['https://example.com/test/path']
        assert issue['references'] == ['https://example.com/ref1', 'https://example.com/ref2']

    def test_group_issues_by_ip(self):
        with BURP_XML_PATH.open('rb') as f:
            issues = self.importer.parse_burp_issues([f])
        grouped = self.importer.group_issues_by_ip(issues)
        
        assert isinstance(grouped, dict) and len(grouped) > 0
        assert all(isinstance(ip_issues, list) and len(ip_issues) > 0 for ip_issues in grouped.values())

    def test_merge_findings_by_type(self):
        issues = [
            {'type': '123456', 'title': 'Test', 'severity': 'medium', 'affected_components': ['https://example.com/path1']},
            {'type': '123456', 'title': 'Test', 'severity': 'medium', 'affected_components': ['https://example.com/path2']}
        ]
        
        merged = self.importer.merge_findings_by_type(issues)
        assert len(merged) == 1 and len(merged[0]['affected_components']) == 2
        assert set(merged[0]['affected_components']) == set(['https://example.com/path1', 'https://example.com/path2'])

    def test_parse_notes_structure(self):
        with BURP_XML_PATH.open('rb') as f:
            notes = self.importer.parse_notes([f])
        
        assert len(notes) > 1 and notes[0].title == 'Burp' and notes[0].icon_emoji == '🟧'
        ip_notes = [n for n in notes if n.parent == notes[0]]
        if ip_notes:
            assert 'Vulnerability overview' in ip_notes[0].text
            assert '| Title | Severity | Affected Components |' in ip_notes[0].text

    def test_empty_file_handling(self):
        file = SimpleUploadedFile("empty.xml", b"""<?xml version="1.0"?><issues burpVersion="2023.7.1"></issues>""")
        
        assert len(self.importer.parse_burp_issues([file])) == 0
        assert len(self.importer.parse_notes([file])) == 0
        assert len(self.importer.parse_findings([file], self.project)) == 0

    def test_issue_ordering_by_severity(self):
        with BURP_XML_PATH.open('rb') as f:
            issues = self.importer.parse_burp_issues([f])
        
        if len(issues) > 1:
            for i in range(len(issues) - 1):
                current, next_issue = issues[i], issues[i + 1]
                if current.get('severity_score', 0) == next_issue.get('severity_score', 0):
                    assert current.get('title', '') <= next_issue.get('title', '')
                else:
                    assert current.get('severity_score', 0) >= next_issue.get('severity_score', 0)

    @pytest.mark.parametrize("severity,expected_score", [
        ("Critical", 5), 
        ("High", 4), 
        ("Medium", 3), 
        ("Low", 2), 
        ("Information", 1), 
        ("info", 1)
    ])
    def test_severity_score_mapping(self, severity, expected_score):
        issue = self.importer.parse_burp_issues([SimpleUploadedFile("test.xml",f"""
        <?xml version="1.0"?>
        <issues burpVersion="2023.7.1">
            <issue>
                <name>Test</name>
                <severity>{severity}</severity>
                <host>https://example.com</host>
                <type>123456</type>
            </issue>
        </issues>
        """.encode())])[0]
        assert issue['severity_score'] == expected_score

    def test_multiple_files_processing(self):
        issues = self.importer.parse_burp_issues([
            SimpleUploadedFile("test1.xml", b"""
                <?xml version="1.0"?>
                <issues burpVersion="2023.7.1">
                    <issue>
                        <name>Issue 1</name>
                        <severity>High</severity>
                        <host>https://another-example.com</host>
                        <type>789012</type>
                    </issue>
                </issues>"""),
            SimpleUploadedFile("test2.xml", b"""
                <?xml version="1.0"?>
                <issues burpVersion="2023.7.1">
                    <issue>
                        <name>Issue 2</name>
                        <severity>High</severity>
                        <host>https://another-example.com</host>
                        <type>789013</type>
                    </issue>
                </issues>""")
        ])
        assert [i['title'] for i in issues] == ['Issue 1', 'Issue 2']
