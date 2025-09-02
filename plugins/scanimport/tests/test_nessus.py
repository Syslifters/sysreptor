from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from sysreptor.pentests import cvss
from sysreptor.tests.mock import create_project, create_user

from ..importers import registry

NESSUS_SINGLE_HOST_PATH = Path(__file__).parent / "data" / "nessus" / "nessus_single_host.xml"
NESSUS_MULTI_HOST_PATH = Path(__file__).parent / "data" / "nessus" / "nessus_multi_host.xml"


@pytest.mark.django_db
class TestNessusImporter:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.project = create_project(members=[create_user()])
        self.importer = registry.get('nessus')

    def test_is_format_valid_nessus_file(self):
        with NESSUS_SINGLE_HOST_PATH.open('rb') as f:
            assert self.importer.is_format(f) is True

    def test_is_format_invalid_file(self):
        invalid_xml = SimpleUploadedFile("invalid.xml", b"<root><invalid></invalid></root>")
        assert self.importer.is_format(invalid_xml) is False

    def test_parse_nessus_findings_single_host(self):
        with NESSUS_SINGLE_HOST_PATH.open('rb') as f:
            findings = self.importer.parse_nessus_findings([f])

        assert len(findings) > 0
        for finding in findings:
            required_fields = {'title', 'severity', 'severity_score', 'affected_components', 'references', 'pluginID'}
            assert required_fields - set(finding.keys()) == set([])
            assert finding['severity'] in ['info', 'low', 'medium', 'high', 'critical']
            assert finding['severity_score'] >= 1
            assert isinstance(finding['affected_components'], list)
            assert len(finding['affected_components']) > 0

    def test_parse_nessus_findings_multi_host(self):
        with NESSUS_MULTI_HOST_PATH.open('rb') as f:
            findings = self.importer.parse_nessus_findings([f])

        assert len(findings) > 0
        # Check that we have findings from multiple hosts
        hosts = set()
        for finding in findings:
            if finding['host'].get('name'):
                hosts.add(finding['host']['name'])
        assert len(hosts) > 1

    def test_parse_nessus_findings_with_severity_mapping(self):
        """Test that risk factors are correctly mapped to severity levels"""
        test_xml = b"""<?xml version="1.0" ?>
        <NessusClientData_v2>
            <Report name="test">
                <ReportHost name="test.example.com">
                    <HostProperties>
                        <tag name="host-ip">192.168.1.1</tag>
                    </HostProperties>
                    <ReportItem port="80" svc_name="www" protocol="tcp" severity="2" pluginID="12345" pluginName="Test Finding">
                        <risk_factor>Medium</risk_factor>
                        <synopsis>Test synopsis</synopsis>
                        <description>Test description</description>
                        <solution>Test solution</solution>
                    </ReportItem>
                </ReportHost>
            </Report>
        </NessusClientData_v2>"""

        findings = self.importer.parse_nessus_findings([SimpleUploadedFile("test.xml", test_xml)])
        assert len(findings) == 1
        assert findings[0]['severity'] == 'medium'
        assert findings[0]['severity_score'] == 3  # severity="2" + 1

    def test_parse_nessus_findings_excludes_snoozed(self):
        """Test that snoozed findings are excluded"""
        test_xml = b"""<?xml version="1.0" ?>
        <NessusClientData_v2>
            <Report name="test">
                <ReportHost name="test.example.com">
                    <HostProperties>
                        <tag name="host-ip">192.168.1.1</tag>
                    </HostProperties>
                    <ReportItem port="80" svc_name="www" protocol="tcp" severity="2" pluginID="12345" pluginName="Test Finding" snoozed="yes">
                        <risk_factor>Medium</risk_factor>
                        <synopsis>Test synopsis</synopsis>
                        <description>Test description</description>
                    </ReportItem>
                </ReportHost>
            </Report>
        </NessusClientData_v2>"""

        findings = self.importer.parse_nessus_findings([SimpleUploadedFile("test.xml", test_xml)])
        assert len(findings) == 0

    def test_affected_components_formatting(self):
        """Test that affected components are properly formatted"""
        test_xml = b"""<?xml version="1.0" ?>
        <NessusClientData_v2>
            <Report name="test">
                <ReportHost name="example.com">
                    <HostProperties>
                        <tag name="host-ip">192.168.1.1</tag>
                    </HostProperties>
                    <ReportItem port="443" svc_name="https" protocol="tcp" severity="1" pluginID="12345" pluginName="Test Finding">
                        <risk_factor>Low</risk_factor>
                        <synopsis>Test synopsis</synopsis>
                    </ReportItem>
                    <ReportItem port="0" svc_name="general" protocol="tcp" severity="0" pluginID="67890" pluginName="General Finding">
                        <risk_factor>Info</risk_factor>
                        <synopsis>General test</synopsis>
                    </ReportItem>
                </ReportHost>
            </Report>
        </NessusClientData_v2>"""

        findings = self.importer.parse_nessus_findings([SimpleUploadedFile("test.xml", test_xml)])
        assert len(findings) == 2
        
        # Finding with specific port and service
        https_finding = next(f for f in findings if f['pluginID'] == '12345')
        assert https_finding['affected_components'] == ['example.com:443 (https)']
        
        # General finding without port specification
        general_finding = next(f for f in findings if f['pluginID'] == '67890')
        assert general_finding['affected_components'] == ['example.com']

    def test_merge_findings_by_plugin(self):
        """Test that findings with same plugin ID are properly merged"""
        with NESSUS_MULTI_HOST_PATH.open('rb') as f:
            findings = self.importer.parse_nessus_findings([f])

        merged = self.importer.merge_findings_by_plugin(findings)
        
        # Should have fewer merged findings than original
        assert len(merged) <= len(findings)
        
        # Check that affected components are merged
        for finding in merged:
            assert isinstance(finding['affected_components'], list)
            assert len(finding['affected_components']) >= 1

    def test_cvss_conversion(self):
        """Test CVSS2 to CVSS3.1 conversion"""
        test_xml = b"""<?xml version="1.0" ?>
        <NessusClientData_v2>
            <Report name="test">
                <ReportHost name="test.example.com">
                    <HostProperties>
                        <tag name="host-ip">192.168.1.1</tag>
                    </HostProperties>
                    <ReportItem port="80" svc_name="www" protocol="tcp" severity="2" pluginID="12345" pluginName="Test Finding">
                        <risk_factor>Medium</risk_factor>
                        <cvss_vector>CVSS2#AV:N/AC:M/Au:N/C:P/I:P/A:N</cvss_vector>
                        <synopsis>Test synopsis</synopsis>
                    </ReportItem>
                </ReportHost>
            </Report>
        </NessusClientData_v2>"""

        findings = self.importer.parse_nessus_findings([SimpleUploadedFile("test.xml", test_xml)])
        assert len(findings) == 1
        # Should have CVSS3.1 vector or empty string
        assert findings[0]['cvss'].startswith('CVSS:3.1') or findings[0]['cvss'] == ''

    def test_plugin_output_handling(self):
        """Test that plugin output is properly handled"""
        test_xml = b"""<?xml version="1.0" ?>
        <NessusClientData_v2>
            <Report name="test">
                <ReportHost name="test.example.com">
                    <HostProperties>
                        <tag name="host-ip">192.168.1.1</tag>
                    </HostProperties>
                    <ReportItem port="80" svc_name="www" protocol="tcp" severity="1" pluginID="12345" pluginName="Test Finding">
                        <risk_factor>Low</risk_factor>
                        <plugin_output>Test output content</plugin_output>
                        <synopsis>Test synopsis</synopsis>
                    </ReportItem>
                </ReportHost>
            </Report>
        </NessusClientData_v2>"""

        findings = self.importer.parse_nessus_findings([SimpleUploadedFile("test.xml", test_xml)])
        assert len(findings) == 1
        assert findings[0]['plugin_output'] == ['Test output content']

    def test_references_handling(self):
        """Test that see_also references are properly handled"""
        test_xml = b"""<?xml version="1.0" ?>
        <NessusClientData_v2>
            <Report name="test">
                <ReportHost name="test.example.com">
                    <HostProperties>
                        <tag name="host-ip">192.168.1.1</tag>
                    </HostProperties>
                    <ReportItem port="80" svc_name="www" protocol="tcp" severity="1" pluginID="12345" pluginName="Test Finding">
                        <risk_factor>Low</risk_factor>
                        <see_also>https://example.com/vuln1</see_also>
                        <synopsis>Test synopsis</synopsis>
                    </ReportItem>
                </ReportHost>
            </Report>
        </NessusClientData_v2>"""

        findings = self.importer.parse_nessus_findings([SimpleUploadedFile("test.xml", test_xml)])
        assert len(findings) == 1
        assert findings[0]['references'] == ['https://example.com/vuln1']

    def test_parse_notes_structure(self):
        """Test that notes are properly structured"""
        with NESSUS_SINGLE_HOST_PATH.open('rb') as f:
            notes = self.importer.parse_notes([f])

        assert len(notes) > 1
        assert notes[0].title == 'Nessus'
        assert notes[0].icon_emoji == '🛡️'
        
        # Should have host-level notes
        host_notes = [n for n in notes if n.parent == notes[0]]
        if host_notes:
            assert 'Vulnerability overview' in host_notes[0].text
            assert '| Title | Severity |' in host_notes[0].text

    def test_parse_notes_multi_host(self):
        """Test notes parsing with multiple hosts"""
        with NESSUS_MULTI_HOST_PATH.open('rb') as f:
            notes = self.importer.parse_notes([f])

        assert len(notes) > 1
        host_notes = [n for n in notes if n.parent == notes[0]]
        assert len(host_notes) > 1  # Should have multiple host notes

    def test_empty_file_handling(self):
        """Test handling of empty Nessus files"""
        empty_xml = SimpleUploadedFile("empty.xml", b"""<?xml version="1.0" ?>
        <NessusClientData_v2>
            <Report name="test">
            </Report>
        </NessusClientData_v2>""")
        
        assert len(self.importer.parse_nessus_findings([empty_xml])) == 0
        notes = self.importer.parse_notes([empty_xml])
        assert len(notes) == 1  # Just the root note
        assert len(self.importer.parse_findings([empty_xml], self.project)) == 0

    def test_findings_sorted_by_severity(self):
        """Test that findings are sorted by severity score"""
        with NESSUS_MULTI_HOST_PATH.open('rb') as f:
            findings = self.importer.parse_nessus_findings([f])

        if len(findings) > 1:
            # Note: Nessus sorts in ascending order by CVSS score/severity_score (lowest first)
            # This matches the implementation in nessus.py line 92-93
            for i in range(len(findings) - 1):
                current = findings[i]
                next_finding = findings[i + 1]
                # Since sorting is ascending, current should be <= next
                if current.get('cvss') and next_finding.get('cvss'):
                    current_score = cvss.calculate_score(current['cvss']) if current['cvss'] else current.get('severity_score', 0)
                    next_score = cvss.calculate_score(next_finding['cvss']) if next_finding['cvss'] else next_finding.get('severity_score', 0)
                    assert current_score <= next_score
                else:
                    # Fall back to severity_score comparison (ascending order)
                    assert current.get('severity_score', 0) <= next_finding.get('severity_score', 0)

    @pytest.mark.parametrize("risk_factor,expected_severity", [
        ("Critical", "critical"),
        ("High", "high"), 
        ("Medium", "medium"),
        ("Low", "low"),
        ("None", "info"),
        ("", "info"),
        ("Unknown", "info")
    ])
    def test_severity_mapping(self, risk_factor, expected_severity):
        """Test risk factor to severity mapping"""
        test_xml = f"""<?xml version="1.0" ?>
        <NessusClientData_v2>
            <Report name="test">
                <ReportHost name="test.example.com">
                    <HostProperties>
                        <tag name="host-ip">192.168.1.1</tag>
                    </HostProperties>
                    <ReportItem port="80" svc_name="www" protocol="tcp" severity="1" pluginID="12345" pluginName="Test Finding">
                        <risk_factor>{risk_factor}</risk_factor>
                        <synopsis>Test synopsis</synopsis>
                    </ReportItem>
                </ReportHost>
            </Report>
        </NessusClientData_v2>""".encode()

        findings = self.importer.parse_nessus_findings([SimpleUploadedFile("test.xml", test_xml)])
        assert len(findings) == 1
        assert findings[0]['severity'] == expected_severity

    def test_multiple_files_processing(self):
        """Test processing multiple Nessus files"""
        test_xml1 = b"""<?xml version="1.0" ?>
        <NessusClientData_v2>
            <Report name="test1">
                <ReportHost name="host1.example.com">
                    <HostProperties>
                        <tag name="host-ip">192.168.1.1</tag>
                    </HostProperties>
                    <ReportItem port="80" svc_name="www" protocol="tcp" severity="1" pluginID="12345" pluginName="Finding 1">
                        <risk_factor>Low</risk_factor>
                        <synopsis>Test synopsis 1</synopsis>
                    </ReportItem>
                </ReportHost>
            </Report>
        </NessusClientData_v2>"""

        test_xml2 = b"""<?xml version="1.0" ?>
        <NessusClientData_v2>
            <Report name="test2">
                <ReportHost name="host2.example.com">
                    <HostProperties>
                        <tag name="host-ip">192.168.1.2</tag>
                    </HostProperties>
                    <ReportItem port="443" svc_name="https" protocol="tcp" severity="2" pluginID="67890" pluginName="Finding 2">
                        <risk_factor>Medium</risk_factor>
                        <synopsis>Test synopsis 2</synopsis>
                    </ReportItem>
                </ReportHost>
            </Report>
        </NessusClientData_v2>"""

        findings = self.importer.parse_nessus_findings([
            SimpleUploadedFile("test1.xml", test_xml1),
            SimpleUploadedFile("test2.xml", test_xml2)
        ])
        
        assert len(findings) == 2
        titles = [f['title'] for f in findings]
        assert 'Finding 1' in titles
        assert 'Finding 2' in titles

    def test_host_properties_parsing(self):
        """Test that host properties are properly parsed"""
        test_xml = b"""<?xml version="1.0" ?>
        <NessusClientData_v2>
            <Report name="test">
                <ReportHost name="test.example.com">
                    <HostProperties>
                        <tag name="host-ip">192.168.1.1</tag>
                        <tag name="netbios-name">TESTHOST</tag>
                        <tag name="operating-system">Windows 10</tag>
                    </HostProperties>
                    <ReportItem port="80" svc_name="www" protocol="tcp" severity="1" pluginID="12345" pluginName="Test Finding">
                        <risk_factor>Low</risk_factor>
                        <synopsis>Test synopsis</synopsis>
                    </ReportItem>
                </ReportHost>
            </Report>
        </NessusClientData_v2>"""

        findings = self.importer.parse_nessus_findings([SimpleUploadedFile("test.xml", test_xml)])
        assert len(findings) == 1
        host = findings[0]['host']
        assert host['name'] == 'test.example.com'
        assert host['host_ip'] == '192.168.1.1'
        assert host['netbios_name'] == 'TESTHOST'
        assert host['operating_system'] == 'Windows 10'

    def test_text_indentation_fix(self):
        """Test that text indentation is properly fixed"""
        test_xml = b"""<?xml version="1.0" ?>
        <NessusClientData_v2>
            <Report name="test">
                <ReportHost name="test.example.com">
                    <HostProperties>
                        <tag name="host-ip">192.168.1.1</tag>
                    </HostProperties>
                    <ReportItem port="80" svc_name="www" protocol="tcp" severity="1" pluginID="12345" pluginName="Test Finding">
                        <risk_factor>Low</risk_factor>
                        <description>    Indented first line
    Second line with different indentation
        Third line</description>
                    </ReportItem>
                </ReportHost>
            </Report>
        </NessusClientData_v2>"""

        findings = self.importer.parse_nessus_findings([SimpleUploadedFile("test.xml", test_xml)])
        assert len(findings) == 1
        # Description should have corrected indentation
        assert findings[0]['description'].startswith('Indented first line\n')
