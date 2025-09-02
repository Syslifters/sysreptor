import json
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from sysreptor.tests.mock import create_project, create_user

from ..importers import registry

SSLYZE_JSON_PATH = Path(__file__).parent / "data" / "sslyze" / "sslyze_v5.json"


@pytest.mark.django_db
class TestSslyzeImporter:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.project = create_project(members=[create_user()])
        self.importer = registry.get('sslyze')

    def test_is_format_valid_sslyze_file(self):
        with SSLYZE_JSON_PATH.open('rb') as f:
            assert self.importer.is_format(f) is True
        
    def test_is_format_invalid_file(self):
        invalid_json = SimpleUploadedFile("invalid.json", b'{"invalid": "data"}')
        assert self.importer.is_format(invalid_json) is False

    def test_parse_sslyze_data_basic(self):
        with SSLYZE_JSON_PATH.open('rb') as f:
            data = self.importer.parse_sslyze_data([SimpleUploadedFile("sslyze.json", f.read())])

        assert len(data) > 0
        for target in data:
            required_keys = {
                'hostname', 'port', 'ip_address', 'protocols', 'ciphers', 
                'certinfo', 'vulnerabilities', 'misconfigurations',
                'has_weak_protocols', 'has_insecure_protocols', 'has_weak_ciphers',
                'has_insecure_ciphers', 'has_cert_issues', 'has_vulnerabilities',
                'has_misconfigurations', 'flag_for_finding', 'protocol_ids'
            }
            assert required_keys - set(target.keys()) == set([])
            assert isinstance(target['protocols'], list)
            assert isinstance(target['ciphers'], list)
            assert isinstance(target['certinfo'], dict)
            assert isinstance(target['vulnerabilities'], dict)
            assert isinstance(target['misconfigurations'], dict)

    def test_get_protocols(self):
        with SSLYZE_JSON_PATH.open('rb') as f:
            import json
            data = json.load(f)
            scan_result = data['server_scan_results'][0]
            protocols = self.importer.get_protocols(scan_result)
        
        assert isinstance(protocols, list)
        for protocol in protocols:
            assert 'id' in protocol
            assert 'name' in protocol
            assert 'is_insecure' in protocol
            assert 'is_weak' in protocol
            assert protocol['id'] in ['sslv2', 'sslv3', 'tlsv1', 'tlsv1_1', 'tlsv1_2', 'tlsv1_3']

    def test_get_ciphers(self):
        with SSLYZE_JSON_PATH.open('rb') as f:
            import json
            data = json.load(f)
            scan_result = data['server_scan_results'][0]
            ciphers = self.importer.get_ciphers(scan_result)
        
        assert isinstance(ciphers, list)
        for cipher in ciphers:
            assert 'name' in cipher
            assert 'protocol' in cipher
            assert 'is_weak' in cipher
            assert 'is_insecure' in cipher
            assert isinstance(cipher['is_weak'], bool)
            assert isinstance(cipher['is_insecure'], bool)

    def test_get_certinfo(self):
        with SSLYZE_JSON_PATH.open('rb') as f:
            import json
            data = json.load(f)
            scan_result = data['server_scan_results'][0]
            certinfo = self.importer.get_certinfo(scan_result)
        
        required_keys = {
            'certificate_matches_hostname', 'has_sha1_in_certificate_chain', 
            'certificate_untrusted', 'has_cert_issues'
        }
        assert required_keys - set(certinfo.keys()) == set([])
        assert isinstance(certinfo['certificate_matches_hostname'], bool)
        assert isinstance(certinfo['has_sha1_in_certificate_chain'], bool)
        assert isinstance(certinfo['certificate_untrusted'], list)
        assert isinstance(certinfo['has_cert_issues'], bool)

    def test_get_vulnerabilities(self):
        with SSLYZE_JSON_PATH.open('rb') as f:
            import json
            data = json.load(f)
            scan_result = data['server_scan_results'][0]
            vulnerabilities = self.importer.get_vulnerabilities(scan_result)
        
        required_keys = {'heartbleed', 'openssl_ccs', 'robot'}
        assert required_keys - set(vulnerabilities.keys()) == set([])
        assert isinstance(vulnerabilities['heartbleed'], bool)
        assert isinstance(vulnerabilities['openssl_ccs'], bool)
        assert isinstance(vulnerabilities['robot'], bool)

    def test_get_misconfigurations(self):
        with SSLYZE_JSON_PATH.open('rb') as f:
            import json
            data = json.load(f)
            scan_result = data['server_scan_results'][0]
            misconfigurations = self.importer.get_misconfigurations(scan_result)
        
        required_keys = {
            'compression', 'downgrade', 'client_renegotiation', 'no_secure_renegotiation'
        }
        assert required_keys - set(misconfigurations.keys()) == set([])
        for key in required_keys:
            assert isinstance(misconfigurations[key], bool)

    def test_weak_cipher_detection(self):
        """Test that weak ciphers are properly identified"""
        test_data = SimpleUploadedFile("test.json", b'''{
            "sslyze_version": "5.0.0",
            "server_scan_results": [{
                "server_location": {
                    "hostname": "test.example.com",
                    "port": 443,
                    "ip_address": "192.168.1.1"
                },
                "scan_result": {
                    "tls_1_2_cipher_suites": {
                        "result": {
                            "accepted_cipher_suites": [{
                                "cipher_suite": {
                                    "openssl_name": "DHE-RSA-DES-CBC3-SHA"
                                }
                            }]
                        }
                    }
                }
            }]
        }''')
        
        data = self.importer.parse_sslyze_data([test_data])
        assert len(data) == 1
        assert data[0]['has_weak_ciphers'] is True
        assert any(c['is_weak'] for c in data[0]['ciphers'])

    def test_insecure_cipher_detection(self):
        """Test that insecure ciphers are properly identified"""
        test_data = SimpleUploadedFile("test.json", b'''{
            "sslyze_version": "5.0.0",
            "server_scan_results": [{
                "server_location": {
                    "hostname": "test.example.com",
                    "port": 443,
                    "ip_address": "192.168.1.1"
                },
                "scan_result": {
                    "tls_1_2_cipher_suites": {
                        "result": {
                            "accepted_cipher_suites": [{
                                "cipher_suite": {
                                    "openssl_name": "NULL-SHA"
                                }
                            }]
                        }
                    }
                }
            }]
        }''')
        
        data = self.importer.parse_sslyze_data([test_data])
        assert len(data) == 1
        assert data[0]['has_insecure_ciphers'] is True
        assert any(c['is_insecure'] for c in data[0]['ciphers'])

    def test_insecure_protocol_detection(self):
        """Test that insecure protocols are properly identified"""
        test_data = SimpleUploadedFile("test.json", b'''{
            "sslyze_version": "5.0.0",
            "server_scan_results": [{
                "server_location": {
                    "hostname": "test.example.com",
                    "port": 443,
                    "ip_address": "192.168.1.1"
                },
                "scan_result": {
                    "ssl_2_0_cipher_suites": {
                        "result": {
                            "accepted_cipher_suites": [{"cipher_suite": {"openssl_name": "DES-CBC3-SHA"}}]
                        }
                    }
                }
            }]
        }''')
        
        data = self.importer.parse_sslyze_data([test_data])
        assert len(data) == 1
        assert data[0]['has_insecure_protocols'] is True
        assert any(p['is_insecure'] for p in data[0]['protocols'])

    def test_weak_protocol_detection(self):
        """Test that weak protocols are properly identified"""
        test_data = SimpleUploadedFile("test.json", b'''{
            "sslyze_version": "5.0.0",
            "server_scan_results": [{
                "server_location": {
                    "hostname": "test.example.com",
                    "port": 443,
                    "ip_address": "192.168.1.1"
                },
                "scan_result": {
                    "tls_1_0_cipher_suites": {
                        "result": {
                            "accepted_cipher_suites": [{"cipher_suite": {"openssl_name": "AES128-SHA"}}]
                        }
                    }
                }
            }]
        }''')
        
        data = self.importer.parse_sslyze_data([test_data])
        assert len(data) == 1
        assert data[0]['has_weak_protocols'] is True
        assert any(p['is_weak'] for p in data[0]['protocols'])

    def test_vulnerability_detection(self):
        """Test vulnerability detection"""
        test_data = SimpleUploadedFile("test.json", b'''{
            "sslyze_version": "5.0.0",
            "server_scan_results": [{
                "server_location": {
                    "hostname": "test.example.com",
                    "port": 443,
                    "ip_address": "192.168.1.1"
                },
                "scan_result": {
                    "heartbleed": {
                        "result": {
                            "is_vulnerable_to_heartbleed": true
                        }
                    },
                    "openssl_ccs_injection": {
                        "result": {
                            "is_vulnerable_to_ccs_injection": false
                        }
                    },
                    "robot": {
                        "result": {
                            "robot_result": "VULNERABLE_WEAK_ORACLE"
                        }
                    }
                }
            }]
        }''')
        
        data = self.importer.parse_sslyze_data([test_data])
        assert len(data) == 1
        target = data[0]
        assert target['vulnerabilities']['heartbleed'] is True
        assert target['vulnerabilities']['openssl_ccs'] is False
        assert target['vulnerabilities']['robot'] is True
        assert target['has_vulnerabilities'] is True

    def test_misconfiguration_detection(self):
        """Test misconfiguration detection"""
        test_data = SimpleUploadedFile("test.json", b'''{
            "sslyze_version": "5.0.0",
            "server_scan_results": [{
                "server_location": {
                    "hostname": "test.example.com",
                    "port": 443,
                    "ip_address": "192.168.1.1"
                },
                "scan_result": {
                    "tls_compression": {
                        "result": {
                            "supports_compression": true
                        }
                    },
                    "tls_fallback_scsv": {
                        "result": {
                            "supports_fallback_scsv": false
                        }
                    },
                    "session_renegotiation": {
                        "result": {
                            "is_vulnerable_to_client_renegotiation_dos": true,
                            "supports_secure_renegotiation": false
                        }
                    }
                }
            }]
        }''')
        
        data = self.importer.parse_sslyze_data([test_data])
        assert len(data) == 1
        target = data[0]
        assert target['misconfigurations']['compression'] is True
        assert target['misconfigurations']['downgrade'] is True
        assert target['misconfigurations']['client_renegotiation'] is True
        assert target['misconfigurations']['no_secure_renegotiation'] is True
        assert target['has_misconfigurations'] is True

    def test_certificate_issues_detection(self):
        """Test certificate issues detection"""
        test_data = SimpleUploadedFile("test.json", b'''{
            "sslyze_version": "5.0.0",
            "server_scan_results": [{
                "server_location": {
                    "hostname": "test.example.com",
                    "port": 443,
                    "ip_address": "192.168.1.1"
                },
                "scan_result": {
                    "certificate_info": {
                        "result": {
                            "certificate_deployments": [{
                                "leaf_certificate_subject_matches_hostname": false,
                                "verified_chain_has_sha1_signature": true,
                                "path_validation_results": [{
                                    "was_validation_successful": false,
                                    "trust_store": {
                                        "name": "Mozilla"
                                    }
                                }]
                            }]
                        }
                    }
                }
            }]
        }''')
        
        data = self.importer.parse_sslyze_data([test_data])
        assert len(data) == 1
        target = data[0]
        assert target['certinfo']['certificate_matches_hostname'] is False
        assert target['certinfo']['has_sha1_in_certificate_chain'] is True
        assert 'Mozilla' in target['certinfo']['certificate_untrusted']
        assert target['certinfo']['has_cert_issues'] is True
        assert target['has_cert_issues'] is True

    def test_parse_notes_structure(self):
        with SSLYZE_JSON_PATH.open('rb') as f:
            notes = self.importer.parse_notes([f])
        
        assert len(notes) >= 1
        assert notes[0].title == 'Sslyze'
        assert notes[0].icon_emoji == '🔒'
        
        # Check if child notes exist for targets
        child_notes = [n for n in notes if n.parent == notes[0]]
        if child_notes:
            for note in child_notes:
                assert 'Protocols' in note.text
                assert 'Certificate Information' in note.text
                assert 'Vulnerabilities' in note.text
                assert 'Misconfigurations' in note.text
                assert 'Weak Cipher Suites' in note.text

    def test_parse_findings_with_issues(self):
        """Test parsing findings when issues are detected"""
        test_data = SimpleUploadedFile("test.json", b'''{
            "sslyze_version": "5.0.0",
            "server_scan_results": [{
                "server_location": {
                    "hostname": "vulnerable.example.com",
                    "port": 443,
                    "ip_address": "192.168.1.1"
                },
                "scan_result": {
                    "ssl_2_0_cipher_suites": {
                        "result": {
                            "accepted_cipher_suites": [{"cipher_suite": {"openssl_name": "DES-CBC3-SHA"}}]
                        }
                    },
                    "heartbleed": {
                        "result": {
                            "is_vulnerable_to_heartbleed": true
                        }
                    }
                }
            }]
        }''')
        
        findings = self.importer.parse_findings([test_data], self.project)
        assert len(findings) == 1
        
        finding = findings[0]
        assert 'Weak TLS setup' in finding.data['title']
        assert finding.data['affected_components'] == ['vulnerable.example.com:443 (192.168.1.1)']

    def test_parse_findings_no_issues(self):
        """Test parsing findings when no issues are detected"""
        test_data = SimpleUploadedFile("test.json", b'''{
            "sslyze_version": "5.0.0",
            "server_scan_results": [{
                "server_location": {
                    "hostname": "secure.example.com",
                    "port": 443,
                    "ip_address": "192.168.1.1"
                },
                "scan_result": {
                    "tls_1_3_cipher_suites": {
                        "result": {
                            "accepted_cipher_suites": [{"cipher_suite": {"openssl_name": "TLS_AES_256_GCM_SHA384"}}]
                        }
                    }
                }
            }]
        }''')
        
        findings = self.importer.parse_findings([test_data], self.project)
        assert len(findings) == 0

    def test_empty_file_handling(self):
        empty_file = SimpleUploadedFile("empty.json", b'{"sslyze_version": "5.0.0", "server_scan_results": []}')
        
        assert len(self.importer.parse_sslyze_data([empty_file])) == 0
        assert len(self.importer.parse_notes([empty_file])) == 1  # Root note only
        assert len(self.importer.parse_findings([empty_file], self.project)) == 0

    def test_multiple_files_processing(self):
        file1 = SimpleUploadedFile("test1.json", b'''{
            "sslyze_version": "5.0.0",
            "server_scan_results": [{
                "server_location": {
                    "hostname": "server1.example.com",
                    "port": 443,
                    "ip_address": "192.168.1.1"
                },
                "scan_result": {
                    "ssl_2_0_cipher_suites": {
                        "result": {
                            "accepted_cipher_suites": [{"cipher_suite": {"openssl_name": "DES-CBC3-SHA"}}]
                        }
                    }
                }
            }]
        }''')
        
        file2 = SimpleUploadedFile("test2.json", b'''{
            "sslyze_version": "5.0.0",
            "server_scan_results": [{
                "server_location": {
                    "hostname": "server2.example.com",
                    "port": 443,
                    "ip_address": "192.168.1.2"
                },
                "scan_result": {
                    "ssl_3_0_cipher_suites": {
                        "result": {
                            "accepted_cipher_suites": [{"cipher_suite": {"openssl_name": "AES128-SHA"}}]
                        }
                    }
                }
            }]
        }''')
        
        data = self.importer.parse_sslyze_data([file1, file2])
        assert len(data) == 2
        hostnames = [target['hostname'] for target in data]
        assert 'server1.example.com' in hostnames
        assert 'server2.example.com' in hostnames

    def test_protocol_ordering(self):
        """Test that protocols are ordered correctly"""
        test_data = SimpleUploadedFile("test.json", b'''{
            "sslyze_version": "5.0.0",
            "server_scan_results": [{
                "server_location": {
                    "hostname": "test.example.com",
                    "port": 443,
                    "ip_address": "192.168.1.1"
                },
                "scan_result": {
                    "tls_1_3_cipher_suites": {
                        "result": {
                            "accepted_cipher_suites": [{"cipher_suite": {"openssl_name": "TLS_AES_256_GCM_SHA384"}}]
                        }
                    },
                    "ssl_2_0_cipher_suites": {
                        "result": {
                            "accepted_cipher_suites": [{"cipher_suite": {"openssl_name": "DES-CBC3-SHA"}}]
                        }
                    },
                    "tls_1_0_cipher_suites": {
                        "result": {
                            "accepted_cipher_suites": [{"cipher_suite": {"openssl_name": "AES128-SHA"}}]
                        }
                    }
                }
            }]
        }''')
        
        data = self.importer.parse_sslyze_data([test_data])
        protocols = data[0]['protocols']
        protocol_ids = [p['id'] for p in protocols]
        
        # Should be ordered from oldest to newest
        expected_order = ['sslv2', 'tlsv1', 'tlsv1_3']
        assert protocol_ids == expected_order

    def test_cipher_ordering(self):
        """Test that ciphers are ordered correctly (insecure first, then weak)"""
        test_data = SimpleUploadedFile("test.json", b'''{
            "sslyze_version": "5.0.0",
            "server_scan_results": [{
                "server_location": {
                    "hostname": "test.example.com",
                    "port": 443,
                    "ip_address": "192.168.1.1"
                },
                "scan_result": {
                    "tls_1_2_cipher_suites": {
                        "result": {
                            "accepted_cipher_suites": [
                                {"cipher_suite": {"openssl_name": "AES128-SHA"}},
                                {"cipher_suite": {"openssl_name": "NULL-SHA"}},
                                {"cipher_suite": {"openssl_name": "DHE-RSA-DES-CBC3-SHA"}}
                            ]
                        }
                    }
                }
            }]
        }''')
        
        data = self.importer.parse_sslyze_data([test_data])
        ciphers = data[0]['ciphers']
        
        # NULL-SHA should be first (insecure), then weak ciphers
        assert ciphers[0]['is_insecure'] is True
        assert ciphers[0]['name'] == 'NULL-SHA'

    def test_flag_for_finding_logic(self):
        """Test that flag_for_finding is set correctly"""
        # Test with no issues
        test_data_secure = SimpleUploadedFile("secure.json", b'''{
            "sslyze_version": "5.0.0",
            "server_scan_results": [{
                "server_location": {
                    "hostname": "secure.example.com",
                    "port": 443,
                    "ip_address": "192.168.1.1"
                },
                "scan_result": {
                    "tls_1_3_cipher_suites": {
                        "result": {
                            "accepted_cipher_suites": [{"cipher_suite": {"openssl_name": "TLS_AES_256_GCM_SHA384"}}]
                        }
                    }
                }
            }]
        }''')
        
        data = self.importer.parse_sslyze_data([test_data_secure])
        assert data[0]['flag_for_finding'] is False
        
        # Test with issues
        test_data_insecure = SimpleUploadedFile("insecure.json", b'''{
            "sslyze_version": "5.0.0",
            "server_scan_results": [{
                "server_location": {
                    "hostname": "insecure.example.com",
                    "port": 443,
                    "ip_address": "192.168.1.1"
                },
                "scan_result": {
                    "ssl_2_0_cipher_suites": {
                        "result": {
                            "accepted_cipher_suites": [{"cipher_suite": {"openssl_name": "DES-CBC3-SHA"}}]
                        }
                    }
                }
            }]
        }''')
        
        data = self.importer.parse_sslyze_data([test_data_insecure])
        assert data[0]['flag_for_finding'] is True

    @pytest.mark.parametrize("protocol_key,expected_id,expected_insecure,expected_weak", [
        ("ssl_2_0_cipher_suites", "sslv2", True, False),
        ("ssl_3_0_cipher_suites", "sslv3", True, False),
        ("tls_1_0_cipher_suites", "tlsv1", False, True),
        ("tls_1_1_cipher_suites", "tlsv1_1", False, True),
        ("tls_1_2_cipher_suites", "tlsv1_2", False, False),
        ("tls_1_3_cipher_suites", "tlsv1_3", False, False),
    ])
    def test_protocol_mapping(self, protocol_key, expected_id, expected_insecure, expected_weak):
        """Test protocol mapping correctness"""
        protocol_info = self.importer.protocol_mapping[protocol_key]
        assert protocol_info['id'] == expected_id
        assert protocol_info['is_insecure'] == expected_insecure
        assert protocol_info['is_weak'] == expected_weak

    @pytest.mark.parametrize("cipher_name,expected_weak,expected_insecure", [
        ("TLS_AES_256_GCM_SHA384", False, False),  # Secure cipher
        ("DHE-RSA-DES-CBC3-SHA", True, False),     # Weak cipher
        ("NULL-SHA", False, True),                 # Insecure cipher
        ("AES128-SHA", True, False),               # Weak cipher
    ])
    def test_cipher_classification(self, cipher_name, expected_weak, expected_insecure):
        """Test cipher classification"""
        is_weak = cipher_name in self.importer.weak_ciphers
        is_insecure = cipher_name in self.importer.insecure_ciphers
        
        assert is_weak == expected_weak
        assert is_insecure == expected_insecure

    def test_notes_flag_in_title(self):
        """Test that notes have flag emoji when issues are found"""
        test_data = SimpleUploadedFile("test.json", b'''{
            "sslyze_version": "5.0.0",
            "server_scan_results": [{
                "server_location": {
                    "hostname": "vulnerable.example.com",
                    "port": 443,
                    "ip_address": "192.168.1.1"
                },
                "scan_result": {
                    "ssl_2_0_cipher_suites": {
                        "result": {
                            "accepted_cipher_suites": [{"cipher_suite": {"openssl_name": "DES-CBC3-SHA"}}]
                        }
                    }
                }
            }]
        }''')
        
        notes = self.importer.parse_notes([test_data])
        child_notes = [n for n in notes if n.parent == notes[0]]
        
        assert len(child_notes) == 1
        assert '🚩' in child_notes[0].title
        assert 'vulnerable.example.com:443' in child_notes[0].title

    def test_finding_content_structure(self):
        """Test the structure and content of generated findings similar to old test"""
        # Create test data matching the old test context
        test_data = SimpleUploadedFile("test.json", b'''{
            "sslyze_version": "5.0.0",
            "server_scan_results": [
                {
                    "server_location": {
                        "hostname": "example.com",
                        "port": 443,
                        "ip_address": "127.0.0.1"
                    },
                    "scan_result": {
                        "ssl_2_0_cipher_suites": {
                            "result": {
                                "accepted_cipher_suites": [{"cipher_suite": {"openssl_name": "DES-CBC3-SHA"}}]
                            }
                        },
                        "heartbleed": {
                            "result": {
                                "is_vulnerable_to_heartbleed": true
                            }
                        },
                        "tls_compression": {
                            "result": {
                                "supports_compression": false
                            }
                        },
                        "tls_fallback_scsv": {
                            "result": {
                                "supports_fallback_scsv": false
                            }
                        },
                        "session_renegotiation": {
                            "result": {
                                "supports_secure_renegotiation": false,
                                "is_vulnerable_to_client_renegotiation_dos": false
                            }
                        },
                        "certificate_info": {
                            "result": {
                                "certificate_deployments": [{
                                    "leaf_certificate_subject_matches_hostname": false,
                                    "path_validation_results": [
                                        {
                                            "was_validation_successful": false,
                                            "trust_store": {"name": "Android"}
                                        },
                                        {
                                            "was_validation_successful": false,
                                            "trust_store": {"name": "Apple"}
                                        }
                                    ]
                                }]
                            }
                        }
                    }
                },
                {
                    "server_location": {
                        "hostname": "www.example.com",
                        "port": 443,
                        "ip_address": "127.0.0.1"
                    },
                    "scan_result": {
                        "ssl_3_0_cipher_suites": {
                            "result": {
                                "accepted_cipher_suites": [{"cipher_suite": {"openssl_name": "AES128-SHA"}}]
                            }
                        },
                        "tls_1_1_cipher_suites": {
                            "result": {
                                "accepted_cipher_suites": [{"cipher_suite": {"openssl_name": "DHE-RSA-AES128-SHA"}}]
                            }
                        },
                        "robot": {
                            "result": {
                                "robot_result": "VULNERABLE_WEAK_ORACLE"
                            }
                        },
                        "tls_compression": {
                            "result": {
                                "supports_compression": true
                            }
                        },
                        "tls_fallback_scsv": {
                            "result": {
                                "supports_fallback_scsv": false
                            }
                        },
                        "session_renegotiation": {
                            "result": {
                                "supports_secure_renegotiation": false,
                                "is_vulnerable_to_client_renegotiation_dos": true
                            }
                        },
                        "certificate_info": {
                            "result": {
                                "certificate_deployments": [{
                                    "leaf_certificate_subject_matches_hostname": true,
                                    "path_validation_results": [
                                        {
                                            "was_validation_successful": false,
                                            "trust_store": {"name": "Android"}
                                        }
                                    ]
                                }]
                            }
                        }
                    }
                },
                {
                    "server_location": {
                        "hostname": "ftp.example.com",
                        "port": 443,
                        "ip_address": "127.0.0.1"
                    },
                    "scan_result": {
                        "tls_1_2_cipher_suites": {
                            "result": {
                                "accepted_cipher_suites": [
                                    {"cipher_suite": {"openssl_name": "DHE-RSA-AES128-SHA"}},
                                    {"cipher_suite": {"openssl_name": "NULL-SHA"}}
                                ]
                            }
                        },
                        "openssl_ccs_injection": {
                            "result": {
                                "is_vulnerable_to_ccs_injection": true
                            }
                        },
                        "certificate_info": {
                            "result": {
                                "certificate_deployments": [{
                                    "leaf_certificate_subject_matches_hostname": false,
                                    "path_validation_results": [
                                        {
                                            "was_validation_successful": true,
                                            "trust_store": {"name": "Mozilla"}
                                        }
                                    ]
                                }]
                            }
                        }
                    }
                }
            ]
        }''')

        findings = self.importer.parse_findings([test_data], self.project)
        assert len(findings) == 1
        
        finding = findings[0]
        finding_text = finding.data.get('description', '') + finding.data.get('summary', '')
        
        # Test that summary contains expected content
        assert 'example.com:443 and 2 other services had a weak TLS setup' in finding.data.get('summary', '')
        
        # Test certificate information in description
        assert 'untrusted by common browsers' in finding_text
        assert 'unmatching hostname; untrusted by Android, Apple' in finding_text
        assert 'untrusted by Android' in finding_text
        
        # Test vulnerabilities table
        assert 'Heartbleed' in finding_text and 'Robot Attack' in finding_text and 'OpenSSL CCS' in finding_text
        
        # Test protocols/ciphers table
        assert 'SSLv2' in finding_text and 'SSLv3' in finding_text and 'TLS 1.0' in finding_text
        
        # Test misconfigurations table  
        assert 'TLS Compression' in finding_text and 'Downgrade' in finding_text

    def test_preprocess_data_structure(self):
        """Test the preprocessed data structure matches expected format"""
        with SSLYZE_JSON_PATH.open('rb') as f:
            data = self.importer.parse_sslyze_data([f])
            
        if data:  # Only test if we have data
            target = data[0]
            # Test that all expected keys exist as in old test
            expected_keys = {
                'hostname', 'port', 'ip_address', 'protocols', 'ciphers',
                'has_weak_protocols', 'has_insecure_protocols', 
                'has_weak_ciphers', 'has_insecure_ciphers',
                'certinfo', 'has_cert_issues', 'vulnerabilities', 
                'has_vulnerabilities', 'misconfigurations', 
                'has_misconfigurations', 'flag_for_finding'
            }
            assert expected_keys.issubset(set(target.keys()))
            
            # Test certificate info structure
            certinfo = target['certinfo']
            assert 'certificate_matches_hostname' in certinfo
            assert 'certificate_untrusted' in certinfo
            assert 'has_sha1_in_certificate_chain' in certinfo
            
            # Test vulnerabilities structure
            vulnerabilities = target['vulnerabilities']
            assert 'heartbleed' in vulnerabilities
            assert 'robot' in vulnerabilities
            assert 'openssl_ccs' in vulnerabilities
            
            # Test misconfigurations structure
            misconfigurations = target['misconfigurations']
            assert 'compression' in misconfigurations
            assert 'downgrade' in misconfigurations
            assert 'client_renegotiation' in misconfigurations
            assert 'no_secure_renegotiation' in misconfigurations

    def test_json_parsing_multiple_inputs(self):
        """Test parsing JSON input similar to old test parse method"""
        # Test single JSON input
        single_input = {
            "sslyze_version": "5.0.0",
            "server_scan_results": [
                {
                    "server_location": {"hostname": "test.com", "port": 443, "ip_address": "1.1.1.1"},
                    "scan_result": {}
                }
            ]
        }
        
        file1 = SimpleUploadedFile("test1.json", json.dumps(single_input).encode())
        data = self.importer.parse_sslyze_data([file1])
        assert len(data) == 1
        
        # Test multiple JSON inputs combined
        file2 = SimpleUploadedFile("test2.json", json.dumps(single_input).encode())
        data = self.importer.parse_sslyze_data([file1, file2])
        assert len(data) == 2

    def test_affected_components_format(self):
        """Test that affected components are formatted correctly"""
        test_data = SimpleUploadedFile("test.json", b'''{
            "sslyze_version": "5.0.0",
            "server_scan_results": [{
                "server_location": {
                    "hostname": "www.example.com",
                    "port": 443,
                    "ip_address": "127.0.0.1"
                },
                "scan_result": {
                    "ssl_2_0_cipher_suites": {
                        "result": {
                            "accepted_cipher_suites": [{"cipher_suite": {"openssl_name": "DES-CBC3-SHA"}}]
                        }
                    }
                }
            }]
        }''')
        
        findings = self.importer.parse_findings([test_data], self.project)
        assert len(findings) == 1
        
        # Test that affected components include both short and long format
        finding_data_str = str(findings[0].data)
        assert 'www.example.com:443 (127.0.0.1)' in finding_data_str
        assert 'www.example.com:443' in finding_data_str

    def test_finding_references(self):
        """Test that findings include expected references"""
        test_data = SimpleUploadedFile("test.json", b'''{
            "sslyze_version": "5.0.0",
            "server_scan_results": [{
                "server_location": {
                    "hostname": "test.example.com",
                    "port": 443,
                    "ip_address": "192.168.1.1"
                },
                "scan_result": {
                    "ssl_2_0_cipher_suites": {
                        "result": {
                            "accepted_cipher_suites": [{"cipher_suite": {"openssl_name": "DES-CBC3-SHA"}}]
                        }
                    }
                }
            }]
        }''')
        
        findings = self.importer.parse_findings([test_data], self.project)
        assert len(findings) == 1
        
        # Check that references are included as in old test
        finding_data = findings[0].data
        assert 'https://ssl-config.mozilla.org/' in str(finding_data)
        assert 'https://ciphersuite.info/' in str(finding_data)

    def test_cvss_score_inclusion(self):
        """Test that CVSS score is included in findings"""
        test_data = SimpleUploadedFile("test.json", b'''{
            "sslyze_version": "5.0.0",
            "server_scan_results": [{
                "server_location": {
                    "hostname": "test.example.com",
                    "port": 443,
                    "ip_address": "192.168.1.1"
                },
                "scan_result": {
                    "ssl_2_0_cipher_suites": {
                        "result": {
                            "accepted_cipher_suites": [{"cipher_suite": {"openssl_name": "DES-CBC3-SHA"}}]
                        }
                    }
                }
            }]
        }''')
        
        findings = self.importer.parse_findings([test_data], self.project)
        assert len(findings) == 1
        
        # Check CVSS score is included
        finding_data = findings[0].data
        assert 'CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:C/C:L/I:L/A:N' in str(finding_data)

    def test_recommendation_inclusion(self):
        """Test that recommendations are included in findings"""
        test_data = SimpleUploadedFile("test.json", b'''{
            "sslyze_version": "5.0.0",
            "server_scan_results": [{
                "server_location": {
                    "hostname": "test.example.com",
                    "port": 443,
                    "ip_address": "192.168.1.1"
                },
                "scan_result": {
                    "ssl_2_0_cipher_suites": {
                        "result": {
                            "accepted_cipher_suites": [{"cipher_suite": {"openssl_name": "DES-CBC3-SHA"}}]
                        }
                    }
                }
            }]
        }''')
        
        findings = self.importer.parse_findings([test_data], self.project)
        assert len(findings) == 1
        
        # Check recommendation is included
        finding_data = findings[0].data
        assert 'Update your TLS setup to protect your data in transit' in str(finding_data)

    def test_complex_scenario_with_all_issues(self):
        """Test a complex scenario with all types of issues like in old test"""
        complex_test_data = SimpleUploadedFile("complex.json", b'''{
            "sslyze_version": "5.0.0",
            "server_scan_results": [{
                "server_location": {
                    "hostname": "complex.example.com",
                    "port": 443,
                    "ip_address": "192.168.1.100"
                },
                "scan_result": {
                    "ssl_2_0_cipher_suites": {
                        "result": {
                            "accepted_cipher_suites": [{"cipher_suite": {"openssl_name": "DES-CBC3-SHA"}}]
                        }
                    },
                    "tls_1_2_cipher_suites": {
                        "result": {
                            "accepted_cipher_suites": [
                                {"cipher_suite": {"openssl_name": "DHE-RSA-AES128-SHA"}},
                                {"cipher_suite": {"openssl_name": "NULL-SHA"}}
                            ]
                        }
                    },
                    "heartbleed": {
                        "result": {"is_vulnerable_to_heartbleed": true}
                    },
                    "robot": {
                        "result": {"robot_result": "VULNERABLE_WEAK_ORACLE"}
                    },
                    "openssl_ccs_injection": {
                        "result": {"is_vulnerable_to_ccs_injection": true}
                    },
                    "tls_compression": {
                        "result": {"supports_compression": true}
                    },
                    "tls_fallback_scsv": {
                        "result": {"supports_fallback_scsv": false}
                    },
                    "session_renegotiation": {
                        "result": {
                            "supports_secure_renegotiation": false,
                            "is_vulnerable_to_client_renegotiation_dos": true
                        }
                    },
                    "certificate_info": {
                        "result": {
                            "certificate_deployments": [{
                                "leaf_certificate_subject_matches_hostname": false,
                                "verified_chain_has_sha1_signature": true,
                                "path_validation_results": [
                                    {"was_validation_successful": false, "trust_store": {"name": "Mozilla"}},
                                    {"was_validation_successful": false, "trust_store": {"name": "Apple"}}
                                ]
                            }]
                        }
                    }
                }
            }]
        }''')
        
        data = self.importer.parse_sslyze_data([complex_test_data])
        assert len(data) == 1
        
        target = data[0]
        
        # Verify all flags are set correctly
        assert target['has_insecure_protocols'] is True  # SSLv2
        assert target['has_weak_ciphers'] is True  # DHE-RSA-AES128-SHA
        assert target['has_insecure_ciphers'] is True  # NULL-SHA
        assert target['has_vulnerabilities'] is True  # All three vulnerabilities
        assert target['has_misconfigurations'] is True  # All misconfigurations
        assert target['has_cert_issues'] is True  # Certificate issues
        assert target['flag_for_finding'] is True  # Should create finding
        
        # Test specific vulnerability detection
        assert target['vulnerabilities']['heartbleed'] is True
        assert target['vulnerabilities']['robot'] is True
        assert target['vulnerabilities']['openssl_ccs'] is True
        
        # Test specific misconfiguration detection
        assert target['misconfigurations']['compression'] is True
        assert target['misconfigurations']['downgrade'] is True
        assert target['misconfigurations']['no_secure_renegotiation'] is True
        assert target['misconfigurations']['client_renegotiation'] is True
        
        # Test certificate issues
        assert target['certinfo']['certificate_matches_hostname'] is False
        assert target['certinfo']['has_sha1_in_certificate_chain'] is True
        assert 'Mozilla' in target['certinfo']['certificate_untrusted']
        assert 'Apple' in target['certinfo']['certificate_untrusted']

    def test_secure_configuration_no_finding(self):
        """Test that secure configurations don't generate findings"""
        secure_test_data = SimpleUploadedFile("secure.json", b'''{
            "sslyze_version": "5.0.0",
            "server_scan_results": [{
                "server_location": {
                    "hostname": "secure.example.com",
                    "port": 443,
                    "ip_address": "192.168.1.200"
                },
                "scan_result": {
                    "tls_1_2_cipher_suites": {
                        "result": {
                            "accepted_cipher_suites": [
                                {"cipher_suite": {"openssl_name": "ECDHE-RSA-AES256-GCM-SHA384"}},
                                {"cipher_suite": {"openssl_name": "ECDHE-RSA-AES128-GCM-SHA256"}}
                            ]
                        }
                    },
                    "tls_1_3_cipher_suites": {
                        "result": {
                            "accepted_cipher_suites": [
                                {"cipher_suite": {"openssl_name": "TLS_AES_256_GCM_SHA384"}},
                                {"cipher_suite": {"openssl_name": "TLS_AES_128_GCM_SHA256"}}
                            ]
                        }
                    },
                    "heartbleed": {
                        "result": {"is_vulnerable_to_heartbleed": false}
                    },
                    "robot": {
                        "result": {"robot_result": "NOT_VULNERABLE"}
                    },
                    "openssl_ccs_injection": {
                        "result": {"is_vulnerable_to_ccs_injection": false}
                    },
                    "tls_compression": {
                        "result": {"supports_compression": false}
                    },
                    "tls_fallback_scsv": {
                        "result": {"supports_fallback_scsv": true}
                    },
                    "session_renegotiation": {
                        "result": {
                            "supports_secure_renegotiation": true,
                            "is_vulnerable_to_client_renegotiation_dos": false
                        }
                    },
                    "certificate_info": {
                        "result": {
                            "certificate_deployments": [{
                                "leaf_certificate_subject_matches_hostname": true,
                                "verified_chain_has_sha1_signature": false,
                                "path_validation_results": [
                                    {"was_validation_successful": true, "trust_store": {"name": "Mozilla"}},
                                    {"was_validation_successful": true, "trust_store": {"name": "Apple"}}
                                ]
                            }]
                        }
                    }
                }
            }]
        }''')
        
        data = self.importer.parse_sslyze_data([secure_test_data])
        assert len(data) == 1
        
        target = data[0]
        
        # Verify all flags are False for secure configuration
        assert target['has_insecure_protocols'] is False
        assert target['has_weak_protocols'] is False
        assert target['has_weak_ciphers'] is False
        assert target['has_insecure_ciphers'] is False
        assert target['has_vulnerabilities'] is False
        assert target['has_misconfigurations'] is False
        assert target['has_cert_issues'] is False
        assert target['flag_for_finding'] is False  # Should NOT create finding
        
        # Verify no findings are generated
        findings = self.importer.parse_findings([secure_test_data], self.project)
        assert len(findings) == 0
