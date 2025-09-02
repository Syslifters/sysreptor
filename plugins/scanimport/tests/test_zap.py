from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from sysreptor.tests.mock import create_project, create_user

from ..importers import registry

ZAP_XML_PATH = Path(__file__).parent / "data" / "zap" / "zap-report.xml"
ZAP_JSON_PATH = Path(__file__).parent / "data" / "zap" / "zap-report.json"


@pytest.mark.django_db
class TestZapImporter:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.project = create_project(members=[create_user()])
        self.importer = registry.get('zap')

    def test_is_format_valid_zap_xml(self):
        with ZAP_XML_PATH.open('rb') as f:
            assert self.importer.is_format(f) is True

    def test_is_format_valid_zap_json(self):
        with ZAP_JSON_PATH.open('rb') as f:
            assert self.importer.is_format(f) is True

    def test_is_format_invalid_file(self):
        invalid_xml = SimpleUploadedFile("invalid.xml", b"<root><invalid></invalid></root>")
        assert self.importer.is_format(invalid_xml) is False

    def test_parse_zap_xml_basic(self):
        with ZAP_XML_PATH.open('rb') as f:
            alerts = self.importer.parse_zap_xml(f)

        assert len(alerts) > 0
        for alert in alerts:
            assert 'site' in alert
            assert 'name' in alert
            assert 'riskcode' in alert
            assert 'instances' in alert
            assert isinstance(alert['instances'], list)

    def test_parse_zap_json_basic(self):
        with ZAP_JSON_PATH.open('rb') as f:
            alerts = self.importer.parse_zap_json(f)

        assert len(alerts) > 0
        for alert in alerts:
            assert 'site' in alert
            assert 'name' in alert
            assert 'riskcode' in alert
            assert 'instances' in alert
            assert isinstance(alert['instances'], list)

    def test_parse_zap_data_xml(self):
        with ZAP_XML_PATH.open('rb') as f:
            alerts = self.importer.parse_zap_data([f])

        assert len(alerts) > 0
        for alert in alerts:
            assert 'severity' in alert
            assert alert['severity'] in ['info', 'low', 'medium', 'high']
            assert 'riskcode' in alert

    def test_parse_zap_data_json(self):
        with ZAP_JSON_PATH.open('rb') as f:
            alerts = self.importer.parse_zap_data([f])

        assert len(alerts) > 0
        for alert in alerts:
            assert 'severity' in alert
            assert alert['severity'] in ['info', 'low', 'medium', 'high']
            assert 'riskcode' in alert

    def test_severity_mapping(self):
        """Test that risk codes are properly mapped to severity levels"""
        test_data = [
            ('0', 'info'),
            ('1', 'low'),
            ('2', 'medium'),
            ('3', 'high'),
            ('999', 'info')  # Default fallback
        ]
        
        for riskcode, expected_severity in test_data:
            alert_xml = SimpleUploadedFile("test.xml", f"""
            <?xml version="1.0"?>
            <OWASPZAPReport programName="OWASP ZAP" version="2.12.0">
                <site name="https://example.com" host="example.com" port="443" ssl="true">
                    <alerts>
                        <alertitem>
                            <pluginid>123</pluginid>
                            <alertRef>123</alertRef>
                            <alert>Test Alert</alert>
                            <name>Test Alert</name>
                            <riskcode>{riskcode}</riskcode>
                            <confidence>2</confidence>
                            <instances>
                                <instance>
                                    <uri>https://example.com/test</uri>
                                    <method>GET</method>
                                </instance>
                            </instances>
                        </alertitem>
                    </alerts>
                </site>
            </OWASPZAPReport>
            """.encode())
            
            alerts = self.importer.parse_zap_data([alert_xml])
            assert len(alerts) == 1
            assert alerts[0]['severity'] == expected_severity

    def test_merge_alerts_by_alertref(self):
        """Test that alerts with the same alertRef are properly merged"""
        alerts = [
            {
                'alertRef': '123',
                'name': 'Test Alert',
                'riskcode': '2',
                'instances': [{'uri': 'https://example.com/path1', 'method': 'GET'}]
            },
            {
                'alertRef': '123',
                'name': 'Test Alert',
                'riskcode': '2',
                'instances': [{'uri': 'https://example.com/path2', 'method': 'POST'}]
            }
        ]
        
        merged = self.importer.merge_alerts(alerts)
        assert len(merged) == 1
        assert len(merged[0]['instances']) == 2
        assert merged[0]['count'] == 2

    def test_parse_notes_structure(self):
        with ZAP_XML_PATH.open('rb') as f:
            notes = self.importer.parse_notes([f])
        
        # Should have a root note and at least one child note
        assert len(notes) > 1
        root_note = notes[0]
        assert root_note.title == 'Zap'
        assert root_note.icon_emoji == '🌩️'
        
        # Check that we have host-level notes
        host_notes = [n for n in notes if n.parent == root_note]
        assert len(host_notes) > 0
        
        # Check that host notes have alert children
        if host_notes:
            alert_notes = [n for n in notes if n.parent == host_notes[0]]
            assert len(alert_notes) > 0

    def test_empty_file_handling(self):
        empty_xml = SimpleUploadedFile("empty.xml", b"""<?xml version="1.0"?>
        <OWASPZAPReport programName="OWASP ZAP" version="2.12.0">
        </OWASPZAPReport>""")
        
        empty_json = SimpleUploadedFile("empty.json", b'{"@programName": "OWASP ZAP", "site": []}')
        
        for empty_file in [empty_xml, empty_json]:
            assert len(self.importer.parse_zap_data([empty_file])) == 0
            assert len(self.importer.parse_notes([empty_file])) == 1  # Only root note

    def test_multiple_files_processing(self):
        """Test processing multiple ZAP files simultaneously"""
        file1 = SimpleUploadedFile("test1.xml", b"""
        <?xml version="1.0"?>
        <OWASPZAPReport programName="OWASP ZAP" version="2.12.0">
            <site name="https://site1.com" host="site1.com" port="443" ssl="true">
                <alerts>
                    <alertitem>
                        <pluginid>123</pluginid>
                        <alertRef>123</alertRef>
                        <alert>Alert 1</alert>
                        <name>Alert 1</name>
                        <riskcode>2</riskcode>
                        <instances>
                            <instance>
                                <uri>https://site1.com/test</uri>
                                <method>GET</method>
                            </instance>
                        </instances>
                    </alertitem>
                </alerts>
            </site>
        </OWASPZAPReport>""")
        
        file2 = SimpleUploadedFile("test2.json", b"""{
            "@programName": "OWASP ZAP",
            "site": [{
                "@name": "https://site2.com",
                "@host": "site2.com", 
                "@port": "443",
                "@ssl": "true",
                "alerts": [{
                    "pluginid": "456",
                    "alertRef": "456",
                    "alert": "Alert 2",
                    "name": "Alert 2",
                    "riskcode": "3",
                    "instances": [{
                        "uri": "https://site2.com/test",
                        "method": "POST"
                    }]
                }]
            }]
        }""")
        
        alerts = self.importer.parse_zap_data([file1, file2])
        assert len(alerts) == 2
        assert alerts[0]['name'] == 'Alert 1'
        assert alerts[1]['name'] == 'Alert 2'

    def test_alert_sorting(self):
        """Test that alerts are sorted by riskcode and alertRef"""
        alerts_xml = SimpleUploadedFile("alerts.xml", b"""
        <?xml version="1.0"?>
        <OWASPZAPReport programName="OWASP ZAP" version="2.12.0">
            <site name="https://example.com" host="example.com" port="443" ssl="true">
                <alerts>
                    <alertitem>
                        <alertRef>200</alertRef>
                        <name>Low Risk Alert</name>
                        <riskcode>1</riskcode>
                        <instances><instance><uri>https://example.com/test1</uri></instance></instances>
                    </alertitem>
                    <alertitem>
                        <alertRef>100</alertRef>
                        <name>High Risk Alert</name>
                        <riskcode>3</riskcode>
                        <instances><instance><uri>https://example.com/test2</uri></instance></instances>
                    </alertitem>
                    <alertitem>
                        <alertRef>150</alertRef>
                        <name>Medium Risk Alert</name>
                        <riskcode>2</riskcode>
                        <instances><instance><uri>https://example.com/test3</uri></instance></instances>
                    </alertitem>
                </alerts>
            </site>
        </OWASPZAPReport>""")
        
        alerts = self.importer.parse_zap_data([alerts_xml])
        
        # Should be sorted by riskcode first, then alertRef
        assert len(alerts) == 3
        assert alerts[0]['riskcode'] == '1'  # Low first
        assert alerts[1]['riskcode'] == '2'  # Then medium  
        assert alerts[2]['riskcode'] == '3'  # Then high

    def test_site_information_parsing(self):
        """Test that site information is correctly parsed and attached to alerts"""
        with ZAP_XML_PATH.open('rb') as f:
            alerts = self.importer.parse_zap_data([f])
        
        for alert in alerts:
            site = alert['site']
            assert 'name' in site
            assert 'host' in site
            assert 'port' in site
            assert 'ssl' in site
            
            # Check that we have valid site data
            assert site['name'].startswith(('http://', 'https://'))
            assert site['port'] in ['80', '443', '8080', '8443'] or site['port'].isdigit()
            assert site['ssl'] in ['true', 'false']

    def test_instances_normalization(self):
        """Test that single instance objects are converted to lists"""
        single_instance_xml = SimpleUploadedFile("single.xml", b"""
        <?xml version="1.0"?>
        <OWASPZAPReport programName="OWASP ZAP" version="2.12.0">
            <site name="https://example.com" host="example.com" port="443" ssl="true">
                <alerts>
                    <alertitem>
                        <alertRef>123</alertRef>
                        <name>Test Alert</name>
                        <riskcode>2</riskcode>
                        <instances>
                            <instance>
                                <uri>https://example.com/test</uri>
                                <method>GET</method>
                                <param>test_param</param>
                                <attack>test_payload</attack>
                            </instance>
                        </instances>
                    </alertitem>
                </alerts>
            </site>
        </OWASPZAPReport>""")
        
        alerts = self.importer.parse_zap_data([single_instance_xml])
        assert len(alerts) == 1
        assert isinstance(alerts[0]['instances'], list)
        assert len(alerts[0]['instances']) == 1

    @pytest.mark.parametrize("format_type,file_path", [
        ("xml", ZAP_XML_PATH),
        ("json", ZAP_JSON_PATH)
    ])
    def test_format_detection(self, format_type, file_path):
        """Test format detection for both XML and JSON ZAP files"""
        if file_path.exists():
            with file_path.open('rb') as f:
                assert self.importer.is_format(f) is True

    def test_json_decode_fallback_to_xml(self):
        """Test that invalid JSON falls back to XML parsing"""
        invalid_json_valid_xml = SimpleUploadedFile("mixed.xml", b"""
        <?xml version="1.0"?>
        <OWASPZAPReport programName="OWASP ZAP" version="2.12.0">
            <site name="https://example.com" host="example.com" port="443" ssl="true">
                <alerts>
                    <alertitem>
                        <alertRef>123</alertRef>
                        <name>Test Alert</name>
                        <riskcode>2</riskcode>
                        <instances>
                            <instance>
                                <uri>https://example.com/test</uri>
                                <method>GET</method>
                            </instance>
                        </instances>
                    </alertitem>
                </alerts>
            </site>
        </OWASPZAPReport>""")
        
        alerts = self.importer.parse_zap_data([invalid_json_valid_xml])
        assert len(alerts) == 1
        assert alerts[0]['name'] == 'Test Alert'
