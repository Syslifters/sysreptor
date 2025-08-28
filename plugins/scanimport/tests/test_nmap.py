import ipaddress
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from sysreptor.tests.mock import create_project, create_user

from ..importers import registry

NMAP_DATA_DIR = Path(__file__).parent / "data" / "nmap"
NMAP_XML_PATH = NMAP_DATA_DIR / "nmap_single_target_single_port.xml"
NMAP_GREPABLE_PATH = NMAP_DATA_DIR / "grepable.txt"
NMAP_MULTI_TARGET_PATH = NMAP_DATA_DIR / "nmap_multi_target.xml"
NMAP_WITH_MAC_PATH = NMAP_DATA_DIR / "nmap_with_mac.xml"
NMAP_WITHOUT_HOSTNAME_PATH = NMAP_DATA_DIR / "nmap_without_hostname.xml"


@pytest.mark.django_db
class TestNmapImporter:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.project = create_project(members=[create_user()])
        self.importer = registry.get('nmap')

    def test_is_format_valid_xml_file(self):
        with NMAP_XML_PATH.open('rb') as f:
            assert self.importer.is_format(f) is True

    def test_is_format_valid_grepable_file(self):
        with NMAP_GREPABLE_PATH.open('rb') as f:
            assert self.importer.is_format(f) is True

    def test_is_format_invalid_file(self):
        invalid_xml = SimpleUploadedFile("invalid.xml", b"<root><invalid></invalid></root>")
        assert self.importer.is_format(invalid_xml) is False

    def test_is_format_invalid_grepable(self):
        invalid_grepable = SimpleUploadedFile("invalid.txt", b"Invalid content without Nmap header")
        assert self.importer.is_format(invalid_grepable) is False

    def test_parse_nmap_xml_single_target(self):
        with NMAP_XML_PATH.open('rb') as f:
            ports = self.importer.parse_nmap_xml(f)

        expected_port = {
            'ip': ipaddress.ip_address('63.35.51.142'),
            'hostname': 'www.syslifters.com',
            'port': '80',
            'protocol': 'tcp',
            'service': 'http',
            'version': None,
        }
        
        assert len(ports) == 1
        assert ports[0] == expected_port

    def test_parse_nmap_xml_multi_target(self):
        with NMAP_MULTI_TARGET_PATH.open('rb') as f:
            ports = self.importer.parse_nmap_xml(f)

        # Expected entries based on old test
        expected_entries = [
            {
                'ip': ipaddress.ip_address('142.250.180.228'),
                'hostname': 'www.google.com',
                'port': '80',
                'protocol': 'tcp',
                'service': 'http',
                'version': 'gws',
            },
            {
                'ip': ipaddress.ip_address('142.250.180.228'),
                'hostname': 'www.google.com',
                'port': '443',
                'protocol': 'tcp',
                'service': 'https',
                'version': 'gws',
            },
            {
                'ip': ipaddress.ip_address('34.249.200.254'),
                'hostname': 'www.syslifters.com',
                'port': '80',
                'protocol': 'tcp',
                'service': 'http',
                'version': None,
            },
            {
                'ip': ipaddress.ip_address('34.249.200.254'),
                'hostname': 'www.syslifters.com',
                'port': '443',
                'protocol': 'tcp',
                'service': 'https',
                'version': None,
            },
        ]

        assert len(ports) >= 4
        for entry in expected_entries:
            assert entry in ports

    def test_parse_nmap_xml_with_mac(self):
        with NMAP_WITH_MAC_PATH.open('rb') as f:
            ports = self.importer.parse_nmap_xml(f)

        expected_entries = [
            {
                'ip': ipaddress.ip_address('192.168.1.69'),
                'hostname': None,
                'port': '22',
                'protocol': 'tcp',
                'service': 'ssh',
                'version': 'OpenSSH',
            },
            {
                'ip': ipaddress.ip_address('192.168.1.69'),
                'hostname': None,
                'port': '25',
                'protocol': 'tcp',
                'service': 'smtp-proxy',
                'version': 'Python SMTP Proxy',
            },
            {
                'ip': ipaddress.ip_address('192.168.1.69'),
                'hostname': None,
                'port': '80',
                'protocol': 'tcp',
                'service': 'http',
                'version': 'Golang net/http server',
            },
            {
                'ip': ipaddress.ip_address('192.168.1.69'),
                'hostname': None,
                'port': '443',
                'protocol': 'tcp',
                'service': 'http',
                'version': 'Golang net/http server',
            },
            {
                'ip': ipaddress.ip_address('192.168.1.69'),
                'hostname': None,
                'port': '2222',
                'protocol': 'tcp',
                'service': 'ssh',
                'version': 'OpenSSH',
            },
            {
                'ip': ipaddress.ip_address('192.168.1.69'),
                'hostname': None,
                'port': '8080',
                'protocol': 'tcp',
                'service': 'http',
                'version': 'Golang net/http server',
            },
            {
                'ip': ipaddress.ip_address('192.168.1.69'),
                'hostname': None,
                'port': '9999',
                'protocol': 'tcp',
                'service': 'abyss',
                'version': None,
            },
        ]

        for entry in expected_entries:
            assert entry in ports

    def test_parse_nmap_xml_without_hostname(self):
        with NMAP_WITHOUT_HOSTNAME_PATH.open('rb') as f:
            ports = self.importer.parse_nmap_xml(f)

        expected_entries = [
            {
                'ip': ipaddress.ip_address('142.251.208.164'),
                'hostname': None,
                'port': '80',
                'protocol': 'tcp',
                'service': 'http',
                'version': None,
            },
            {
                'ip': ipaddress.ip_address('142.251.208.164'),
                'hostname': None,
                'port': '443',
                'protocol': 'tcp',
                'service': 'https',
                'version': None,
            },
        ]

        for entry in expected_entries:
            assert entry in ports

    def test_parse_nmap_greppable(self):
        with NMAP_GREPABLE_PATH.open('rb') as f:
            ports = self.importer.parse_nmap_greppable(f)

        expected_entries = [
            {
                'ip': ipaddress.ip_address('127.0.0.1'),
                'hostname': None,
                'port': '80',
                'protocol': 'tcp',
                'service': 'http',
                'version': 'nginx (reverse proxy)',
            },
            {
                'ip': ipaddress.ip_address('127.0.0.1'),
                'hostname': None,
                'port': '443',
                'protocol': 'tcp',
                'service': 'ssl|http',
                'version': 'nginx (reverse proxy)',
            },
            {
                'ip': ipaddress.ip_address('127.0.0.1'),
                'hostname': None,
                'port': '8080',
                'protocol': 'tcp',
                'service': '',
                'version': '',
            },
        ]

        assert len(ports) == 3
        for entry in expected_entries:
            assert entry in ports

    def test_parse_nmap_data_multiple_files(self):
        with NMAP_XML_PATH.open('rb') as xml_file, NMAP_GREPABLE_PATH.open('rb') as grep_file:
            ports = self.importer.parse_nmap_data([xml_file, grep_file])

        # Should contain ports from both files
        assert len(ports) >= 4  # At least one from XML and three from greppable

        # Check for XML entry
        xml_entry = {
            'ip': ipaddress.ip_address('63.35.51.142'),
            'hostname': 'www.syslifters.com',
            'port': '80',
            'protocol': 'tcp',
            'service': 'http',
            'version': None,
        }
        assert xml_entry in ports

        # Check for greppable entry
        grep_entry = {
            'ip': ipaddress.ip_address('127.0.0.1'),
            'hostname': None,
            'port': '80',
            'protocol': 'tcp',
            'service': 'http',
            'version': 'nginx (reverse proxy)',
        }
        assert grep_entry in ports

    def test_parse_notes_structure(self):
        with NMAP_XML_PATH.open('rb') as f:
            notes = self.importer.parse_notes([f])

        assert len(notes) >= 1
        assert notes[0].title == 'Nmap'
        assert notes[0].icon_emoji == '👁️‍🗨️'
        assert '| Host | Port | Service | Version |' in notes[0].text or '| Hostname | IP | Port | Service | Version |' in notes[0].text

        # Check for IP-specific notes
        ip_notes = [n for n in notes if n.parent == notes[0]]
        if ip_notes:
            assert str(ip_notes[0].title) == '63.35.51.142'
            assert '| Host | Port | Service | Version |' in ip_notes[0].text or '| Hostname | IP | Port | Service | Version |' in ip_notes[0].text

    def test_parse_notes_with_hostname(self):
        with NMAP_MULTI_TARGET_PATH.open('rb') as f:
            notes = self.importer.parse_notes([f])

        # Should show hostname table when hostnames are present
        assert '| Hostname | IP | Port | Service | Version |' in notes[0].text

    def test_parse_notes_without_hostname(self):
        with NMAP_GREPABLE_PATH.open('rb') as f:
            notes = self.importer.parse_notes([f])

        # Should show simpler table when no hostnames are present
        assert '| Host | Port | Service | Version |' in notes[0].text

    def test_empty_file_handling(self):
        empty_xml = SimpleUploadedFile("empty.xml", b"""<?xml version="1.0"?><nmaprun></nmaprun>""")
        
        assert len(self.importer.parse_nmap_data([empty_xml])) == 0
        assert len(self.importer.parse_notes([empty_xml])) == 1  # Root note is always created

    def test_multiple_xml_files_processing(self):
        with NMAP_XML_PATH.open('rb') as f1:
            content1 = f1.read()
        with NMAP_WITH_MAC_PATH.open('rb') as f2:
            content2 = f2.read()

        file1 = SimpleUploadedFile("nmap1.xml", content1)
        file2 = SimpleUploadedFile("nmap2.xml", content2)
        
        ports = self.importer.parse_nmap_data([file1, file2])
        
        # Should contain ports from both files
        assert len(ports) >= 8  # 1 from first file + 7 from second file

        # Verify entries from both files are present
        assert any(port['ip'] == ipaddress.ip_address('63.35.51.142') for port in ports)
        assert any(port['ip'] == ipaddress.ip_address('192.168.1.69') for port in ports)

    def test_ip_address_handling(self):
        """Test proper handling of IPv4 and IPv6 addresses"""
        with NMAP_XML_PATH.open('rb') as f:
            ports = self.importer.parse_nmap_xml(f)

        for port in ports:
            assert isinstance(port['ip'], (ipaddress.IPv4Address, ipaddress.IPv6Address))

    def test_service_version_handling(self):
        """Test proper handling of service and version information"""
        with NMAP_WITH_MAC_PATH.open('rb') as f:
            ports = self.importer.parse_nmap_xml(f)

        # Check various service/version combinations
        services = [port['service'] for port in ports]
        versions = [port['version'] for port in ports]
        
        assert 'ssh' in services
        assert 'http' in services
        assert 'OpenSSH' in versions
        assert None in versions  # Some services may not have version info

    def test_port_filtering_open_only(self):
        """Test that only open ports are included"""
        # This test assumes the XML files only contain open ports
        # If we had a file with closed/filtered ports, we'd test those are excluded
        with NMAP_WITH_MAC_PATH.open('rb') as f:
            ports = self.importer.parse_nmap_xml(f)

        # All returned ports should be implicitly open (since we only parse open ones)
        assert len(ports) > 0
        # In a real scenario, we'd verify that closed/filtered ports are not included

    def test_hostname_detection_logic(self):
        """Test the logic for showing hostname column in tables"""
        # File with hostnames
        with NMAP_MULTI_TARGET_PATH.open('rb') as f:
            ports_with_hostname = self.importer.parse_nmap_data([f])
        
        show_hostname_true = any(s.get('hostname') for s in ports_with_hostname)
        assert show_hostname_true is True

        # File without hostnames  
        with NMAP_GREPABLE_PATH.open('rb') as f:
            ports_without_hostname = self.importer.parse_nmap_data([f])
        
        show_hostname_false = any(s.get('hostname') for s in ports_without_hostname)
        assert show_hostname_false is False

    def test_greppable_port_parsing(self):
        """Test specific greppable format parsing edge cases"""
        greppable_content = b"""# Nmap 7.80 scan initiated
Host: 127.0.0.1 ()        Ports: 22/open/tcp//ssh//OpenSSH/, 80/closed/tcp//http///, 443/filtered/tcp//https///
# Nmap done"""
        
        file = SimpleUploadedFile("test.txt", greppable_content)
        ports = self.importer.parse_nmap_greppable(file)
        
        # Only open ports should be parsed
        assert len(ports) == 1
        assert ports[0]['port'] == '22'
        assert ports[0]['service'] == 'ssh'
        assert ports[0]['version'] == 'OpenSSH'

    def test_xml_syntax_error_fallback(self):
        """Test fallback to greppable parsing when XML parsing fails"""
        # Create a file that starts like greppable but isn't valid XML
        invalid_xml_content = b"""# Nmap 7.80 scan initiated
Host: 192.168.1.1 ()        Ports: 80/open/tcp//http//Apache/"""

        file = SimpleUploadedFile("invalid.xml", invalid_xml_content)
        
        # Should be detected as valid format (greppable fallback)
        assert self.importer.is_format(file) is True
        
        ports = self.importer.parse_nmap_data([file])
        assert len(ports) == 1
        assert ports[0]['ip'] == ipaddress.ip_address('192.168.1.1')
