from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from sysreptor.tests.mock import create_project, create_user

from ..importers import registry

QUALYS_VULN_PATH = Path(__file__).parent / "data" / "qualys" / "vuln_scan.xml"
QUALYS_WAS_PATH = Path(__file__).parent / "data" / "qualys" / "webapp_scan.xml"


@pytest.mark.django_db
class TestQualysImporter:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.project = create_project(members=[create_user()])
        self.importer = registry.get('qualys')

    def test_is_format_valid_vuln_scan_file(self):
        with QUALYS_VULN_PATH.open('rb') as f:
            assert self.importer.is_format(f) is True
        
    def test_is_format_valid_webapp_scan_file(self):
        with QUALYS_WAS_PATH.open('rb') as f:
            assert self.importer.is_format(f) is True

    def test_is_format_invalid_file(self):
        invalid_xml = SimpleUploadedFile("invalid.xml", b"<root><invalid></invalid></root>")
        assert self.importer.is_format(invalid_xml) is False

    def test_parse_qualys_findings_vuln_scan_basic(self):
        with QUALYS_VULN_PATH.open('rb') as f:
            findings = self.importer.parse_qualys_findings([SimpleUploadedFile("vuln_scan.xml", f.read())])

        assert len(findings) > 0
        for finding in findings:
            assert {'title', 'severity', 'severity_score', 'affected_components', 'target'} - set(finding.keys()) == set([])
            assert finding['severity'] in ['info', 'low', 'medium', 'high', 'critical']
            assert finding['severity_score'] >= 1
            assert isinstance(finding['affected_components'], list)
            assert 'ip' in finding['target']
            assert 'hostname' in finding['target']

    def test_parse_qualys_findings_webapp_scan_basic(self):
        with QUALYS_WAS_PATH.open('rb') as f:
            findings = self.importer.parse_qualys_findings([SimpleUploadedFile("webapp_scan.xml", f.read())])

        assert len(findings) > 0
        for finding in findings:
            assert {'title', 'severity', 'severity_score', 'affected_components', 'target'} - set(finding.keys()) == set([])
            assert finding['severity'] in ['info', 'low', 'medium', 'high', 'critical']
            assert finding['severity_score'] >= 1
            assert isinstance(finding['affected_components'], list)
            assert 'hostname' in finding['target']

    def test_target_information_vuln_scan(self):
        """Test proper handling of target information for vulnerability scans"""
        with QUALYS_VULN_PATH.open('rb') as f:
            findings = self.importer.parse_qualys_findings([f])
        
        for finding in findings:
            target = finding.get('target', {})
            assert isinstance(target.get('ip'), (str, type(None)))
            assert isinstance(target.get('hostname'), (str, type(None)))
            assert isinstance(target.get('port'), (str, type(None)))
            assert isinstance(target.get('protocol'), (str, type(None)))
            
            # At least one of IP or hostname should be present
            assert target.get('ip') or target.get('hostname')

    def test_target_information_webapp_scan(self):
        """Test proper handling of target information for web application scans"""
        with QUALYS_WAS_PATH.open('rb') as f:
            findings = self.importer.parse_qualys_findings([f])
        
        for finding in findings:
            target = finding.get('target', {})
            assert target.get('hostname') is not None
            assert isinstance(target.get('port'), int)
            assert target.get('protocol') == 'tcp'

    def test_affected_components_format(self):
        """Test that affected components are properly formatted"""
        with QUALYS_VULN_PATH.open('rb') as f:
            findings = self.importer.parse_qualys_findings([f])
        
        for finding in findings:
            for component in finding.get('affected_components', []):
                assert isinstance(component, str) and len(component) > 0

    def test_merge_findings(self):
        """Test finding merging functionality"""
        test_findings = [
            {
                'number': '12345',
                'title': 'Test Vulnerability',
                'severity': 'high',
                'severity_score': 4,
                'affected_components': ['host1.example.com:80']
            },
            {
                'number': '12345',
                'title': 'Test Vulnerability',
                'severity': 'high',
                'severity_score': 4,
                'affected_components': ['host2.example.com:80']
            }
        ]
        
        merged = self.importer.merge_findings(test_findings)
        assert len(merged) == 1
        assert len(merged[0]['affected_components']) == 2
        assert set(merged[0]['affected_components']) == {'host1.example.com:80', 'host2.example.com:80'}

    def test_severity_score_mapping_vuln_scan(self):
        """Test severity score mapping for vulnerability scans"""
        findings = self.importer.parse_qualys_findings([SimpleUploadedFile("test.xml", b"""
        <?xml version="1.0" encoding="UTF-8"?>
        <SCAN>
            <IP value="192.168.1.1" name="test.example.com">
                <VULNS>
                    <CAT value="Test Category" port="80" protocol="tcp">
                        <VULN number="12345" severity="5">
                            <TITLE>High Severity Test</TITLE>
                            <DIAGNOSIS>Test diagnosis</DIAGNOSIS>
                            <CONSEQUENCE>Test consequence</CONSEQUENCE>
                            <SOLUTION>Test solution</SOLUTION>
                        </VULN>
                        <VULN number="12346" severity="3">
                            <TITLE>Medium Severity Test</TITLE>
                            <DIAGNOSIS>Test diagnosis</DIAGNOSIS>
                            <CONSEQUENCE>Test consequence</CONSEQUENCE>
                            <SOLUTION>Test solution</SOLUTION>
                        </VULN>
                        <VULN number="12347" severity="1">
                            <TITLE>Info Severity Test</TITLE>
                            <DIAGNOSIS>Test diagnosis</DIAGNOSIS>
                            <CONSEQUENCE>Test consequence</CONSEQUENCE>
                            <SOLUTION>Test solution</SOLUTION>
                        </VULN>
                    </CAT>
                </VULNS>
            </IP>
        </SCAN>
        """)])

        assert len(findings) == 3
        assert findings[0]['severity_score'] == 5  # High should be first due to sorting
        assert findings[0]['severity'] == 'critical'
        assert findings[1]['severity_score'] == 3
        assert findings[1]['severity'] == 'medium'
        assert findings[2]['severity_score'] == 1
        assert findings[2]['severity'] == 'info'

    def test_severity_score_mapping_webapp_scan(self):
        """Test severity score mapping for web application scans"""
        findings = self.importer.parse_qualys_findings([SimpleUploadedFile("test.xml", b"""
        <?xml version='1.0' encoding='UTF-8'?>
        <WAS_SCAN_REPORT>
            <GLOSSARY>
                <QID_LIST>
                    <QID>
                        <QID>150001</QID>
                        <TITLE>Test High Vulnerability</TITLE>
                        <SOLUTION>Test solution</SOLUTION>
                        <IMPACT>Test impact</IMPACT>
                    </QID>
                    <QID>
                        <QID>150002</QID>
                        <TITLE>Test Low Vulnerability</TITLE>
                        <SOLUTION>Test solution</SOLUTION>
                        <IMPACT>Test impact</IMPACT>
                    </QID>
                </QID_LIST>
            </GLOSSARY>
            <RESULTS>
                <VULNERABILITY_LIST>
                    <VULNERABILITY>
                        <QID>150001</QID>
                        <URL>https://example.com/test1</URL>
                        <SEVERITY>4</SEVERITY>
                    </VULNERABILITY>
                    <VULNERABILITY>
                        <QID>150002</QID>
                        <URL>https://example.com/test2</URL>
                        <SEVERITY>2</SEVERITY>
                    </VULNERABILITY>
                </VULNERABILITY_LIST>
            </RESULTS>
        </WAS_SCAN_REPORT>
        """)])

        assert len(findings) == 2
        assert findings[0]['severity_score'] == 4  # High should be first due to sorting
        assert findings[0]['severity'] == 'high'
        assert findings[1]['severity_score'] == 2
        assert findings[1]['severity'] == 'low'

    def test_parse_notes_structure(self):
        with QUALYS_VULN_PATH.open('rb') as f:
            notes = self.importer.parse_notes([f])
        
        assert len(notes) > 1 
        assert notes[0].title == 'Qualys' 
        assert notes[0].icon_emoji == '🛡️'
        
        # Check for host-specific notes
        host_notes = [n for n in notes if n.parent == notes[0]]
        if host_notes:
            assert 'Vulnerability overview' in host_notes[0].text
            assert '| Title | Severity |' in host_notes[0].text

    def test_empty_file_handling(self):
        empty_vuln_file = SimpleUploadedFile("empty_vuln.xml", b"""<?xml version="1.0" encoding="UTF-8"?><SCAN></SCAN>""")
        empty_was_file = SimpleUploadedFile("empty_was.xml", b"""<?xml version='1.0' encoding='UTF-8'?><WAS_SCAN_REPORT><RESULTS><VULNERABILITY_LIST></VULNERABILITY_LIST></RESULTS></WAS_SCAN_REPORT>""")
        
        assert len(self.importer.parse_qualys_findings([empty_vuln_file])) == 0
        assert len(self.importer.parse_qualys_findings([empty_was_file])) == 0
        assert len(self.importer.parse_notes([empty_vuln_file])) == 0
        assert len(self.importer.parse_findings([empty_vuln_file], self.project)) == 0

    def test_findings_ordering_by_severity(self):
        with QUALYS_VULN_PATH.open('rb') as f:
            findings = self.importer.parse_qualys_findings([f])
        
        if len(findings) > 1:
            for i in range(len(findings) - 1):
                current, next_finding = findings[i], findings[i + 1]
                if current.get('severity_score', 0) == next_finding.get('severity_score', 0):
                    # Same severity, check title ordering
                    assert current.get('title', '') <= next_finding.get('title', '')
                else:
                    # Different severity, check severity ordering (high to low)
                    assert current.get('severity_score', 0) >= next_finding.get('severity_score', 0)

    def test_field_mapping_vuln_scan(self):
        """Test proper field mapping for vulnerability scans"""
        findings = self.importer.parse_qualys_findings([SimpleUploadedFile("test.xml", b"""
        <?xml version="1.0" encoding="UTF-8"?>
        <SCAN>
            <IP value="192.168.1.1" name="test.example.com">
                <VULNS>
                    <CAT value="Test Category" port="443" protocol="tcp">
                        <VULN number="12345" severity="4">
                            <TITLE>Test Field Mapping</TITLE>
                            <DIAGNOSIS>This is the diagnosis field</DIAGNOSIS>
                            <CONSEQUENCE>This is the consequence field</CONSEQUENCE>
                            <SOLUTION>This is the solution field</SOLUTION>
                        </VULN>
                    </CAT>
                </VULNS>
            </IP>
        </SCAN>
        """)])

        assert len(findings) == 1
        finding = findings[0]
        assert finding['title'] == 'Test Field Mapping'
        assert finding['description'] == 'This is the diagnosis field'
        assert finding['summary'] == 'This is the consequence field'
        assert finding['recommendation'] == 'This is the solution field'
        assert finding['number'] == '12345'

    def test_field_mapping_webapp_scan(self):
        """Test proper field mapping for web application scans"""
        findings = self.importer.parse_qualys_findings([SimpleUploadedFile("test.xml", b"""
        <?xml version='1.0' encoding='UTF-8'?>
        <WAS_SCAN_REPORT>
            <GLOSSARY>
                <QID_LIST>
                    <QID>
                        <QID>150001</QID>
                        <TITLE>Test Web App Vulnerability</TITLE>
                        <SOLUTION>Test web app solution</SOLUTION>
                        <IMPACT>Test web app impact</IMPACT>
                    </QID>
                </QID_LIST>
            </GLOSSARY>
            <RESULTS>
                <VULNERABILITY_LIST>
                    <VULNERABILITY>
                        <QID>150001</QID>
                        <URL>https://example.com:8080/test</URL>
                        <SEVERITY>3</SEVERITY>
                    </VULNERABILITY>
                </VULNERABILITY_LIST>
            </RESULTS>
        </WAS_SCAN_REPORT>
        """)])

        assert len(findings) == 1
        finding = findings[0]
        assert finding['title'] == 'Test Web App Vulnerability'
        assert finding['summary'] == 'Test web app impact'
        assert finding['recommendation'] == 'Test web app solution'
        assert finding['number'] == '150001'
        assert finding['url'] == 'https://example.com:8080/test'
        assert finding['target']['hostname'] == 'example.com'
        assert finding['target']['port'] == 8080

    def test_multiple_files_processing(self):
        """Test processing multiple Qualys files"""
        vuln_findings = self.importer.parse_qualys_findings([
            SimpleUploadedFile("test1.xml", b"""
                <?xml version="1.0" encoding="UTF-8"?>
                <SCAN>
                    <IP value="192.168.1.1" name="host1.example.com">
                        <VULNS>
                            <CAT value="Test Category" port="80" protocol="tcp">
                                <VULN number="11111" severity="4">
                                    <TITLE>Vulnerability 1</TITLE>
                                    <DIAGNOSIS>Test diagnosis 1</DIAGNOSIS>
                                    <CONSEQUENCE>Test consequence 1</CONSEQUENCE>
                                    <SOLUTION>Test solution 1</SOLUTION>
                                </VULN>
                            </CAT>
                        </VULNS>
                    </IP>
                </SCAN>"""),
            SimpleUploadedFile("test2.xml", b"""
                <?xml version="1.0" encoding="UTF-8"?>
                <SCAN>
                    <IP value="192.168.1.2" name="host2.example.com">
                        <VULNS>
                            <CAT value="Test Category" port="443" protocol="tcp">
                                <VULN number="22222" severity="3">
                                    <TITLE>Vulnerability 2</TITLE>
                                    <DIAGNOSIS>Test diagnosis 2</DIAGNOSIS>
                                    <CONSEQUENCE>Test consequence 2</CONSEQUENCE>
                                    <SOLUTION>Test solution 2</SOLUTION>
                                </VULN>
                            </CAT>
                        </VULNS>
                    </IP>
                </SCAN>""")
        ])
        
        assert len(vuln_findings) == 2
        titles = [f['title'] for f in vuln_findings]
        assert 'Vulnerability 1' in titles
        assert 'Vulnerability 2' in titles

    def test_url_parsing_webapp_scan(self):
        """Test URL parsing for web application scans"""
        findings = self.importer.parse_qualys_findings([SimpleUploadedFile("test.xml", b"""
        <?xml version='1.0' encoding='UTF-8'?>
        <WAS_SCAN_REPORT>
            <GLOSSARY>
                <QID_LIST>
                    <QID>
                        <QID>150001</QID>
                        <TITLE>HTTPS Test</TITLE>
                        <SOLUTION>Test solution</SOLUTION>
                        <IMPACT>Test impact</IMPACT>
                    </QID>
                    <QID>
                        <QID>150002</QID>
                        <TITLE>HTTP Test</TITLE>
                        <SOLUTION>Test solution</SOLUTION>
                        <IMPACT>Test impact</IMPACT>
                    </QID>
                </QID_LIST>
            </GLOSSARY>
            <RESULTS>
                <VULNERABILITY_LIST>
                    <VULNERABILITY>
                        <QID>150001</QID>
                        <URL>https://secure.example.com/path</URL>
                        <SEVERITY>3</SEVERITY>
                    </VULNERABILITY>
                    <VULNERABILITY>
                        <QID>150002</QID>
                        <URL>http://insecure.example.com:8080/path</URL>
                        <SEVERITY>2</SEVERITY>
                    </VULNERABILITY>
                </VULNERABILITY_LIST>
            </RESULTS>
        </WAS_SCAN_REPORT>
        """)])

        assert len(findings) == 2
        
        https_finding = next(f for f in findings if f['title'] == 'HTTPS Test')
        assert https_finding['target']['hostname'] == 'secure.example.com'
        assert https_finding['target']['port'] == 443  # Default HTTPS port
        assert https_finding['affected_components'] == ['https://secure.example.com/path']

        http_finding = next(f for f in findings if f['title'] == 'HTTP Test')
        assert http_finding['target']['hostname'] == 'insecure.example.com'
        assert http_finding['target']['port'] == 8080  # Explicit port
        assert http_finding['affected_components'] == ['http://insecure.example.com:8080/path']

    @pytest.mark.parametrize("severity,expected_score,expected_level", [
        ("5", 5, "critical"),
        ("4", 4, "high"), 
        ("3", 3, "medium"), 
        ("2", 2, "low"), 
        ("1", 1, "info"),
        (None, 1, "info")  # Test null severity handling
    ])
    def test_severity_mapping(self, severity, expected_score, expected_level):
        """Test severity score and level mapping"""
        severity_attr = f'severity="{severity}"' if severity else ''
        findings = self.importer.parse_qualys_findings([SimpleUploadedFile("test.xml", f"""
        <?xml version="1.0" encoding="UTF-8"?>
        <SCAN>
            <IP value="192.168.1.1" name="test.example.com">
                <VULNS>
                    <CAT value="Test Category" port="80" protocol="tcp">
                        <VULN number="12345" {severity_attr}>
                            <TITLE>Test Severity</TITLE>
                            <DIAGNOSIS>Test diagnosis</DIAGNOSIS>
                            <CONSEQUENCE>Test consequence</CONSEQUENCE>
                            <SOLUTION>Test solution</SOLUTION>
                        </VULN>
                    </CAT>
                </VULNS>
            </IP>
        </SCAN>
        """.encode())])
        
        assert len(findings) == 1
        finding = findings[0]
        assert finding['severity_score'] == expected_score
        assert finding['severity'] == expected_level

    def test_port_handling_vuln_scan(self):
        """Test port handling in vulnerability scans"""
        findings = self.importer.parse_qualys_findings([SimpleUploadedFile("test.xml", b"""
        <?xml version="1.0" encoding="UTF-8"?>
        <SCAN>
            <IP value="192.168.1.1" name="test.example.com">
                <VULNS>
                    <CAT value="With Port" port="8443" protocol="tcp">
                        <VULN number="12345" severity="3">
                            <TITLE>Test With Port</TITLE>
                            <DIAGNOSIS>Test diagnosis</DIAGNOSIS>
                            <CONSEQUENCE>Test consequence</CONSEQUENCE>
                            <SOLUTION>Test solution</SOLUTION>
                        </VULN>
                    </CAT>
                    <CAT value="Without Port" protocol="tcp">
                        <VULN number="12346" severity="3">
                            <TITLE>Test Without Port</TITLE>
                            <DIAGNOSIS>Test diagnosis</DIAGNOSIS>
                            <CONSEQUENCE>Test consequence</CONSEQUENCE>
                            <SOLUTION>Test solution</SOLUTION>
                        </VULN>
                    </CAT>
                </VULNS>
            </IP>
        </SCAN>
        """)])

        assert len(findings) == 2
        
        with_port = next(f for f in findings if f['title'] == 'Test With Port')
        assert with_port['target']['port'] == '8443'
        assert with_port['affected_components'] == ['test.example.com:8443']

        without_port = next(f for f in findings if f['title'] == 'Test Without Port')
        assert without_port['target']['port'] is None
        assert without_port['affected_components'] == ['test.example.com']
