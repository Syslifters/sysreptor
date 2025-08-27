import itertools
import json
import textwrap

from sysreptor.pentests.models import (
    FindingTemplateTranslation,
    Language,
    ProjectNotebookPage,
)

from ..utils import render_template_string
from .base import BaseImporter, fallback_template


class SslyzeImporter(BaseImporter):
    id = 'sslyze'

    protocol_mapping = {
        "ssl_2_0_cipher_suites": {"id": "sslv2", "name": "SSLv2", "is_insecure": True, "is_weak": False},
        "ssl_3_0_cipher_suites": {"id": "sslv3", "name": "SSLv3", "is_insecure": True, "is_weak": False},
        "tls_1_0_cipher_suites": {"id": "tlsv1", "name": "TLS 1.0", "is_insecure": False, "is_weak": True},
        "tls_1_1_cipher_suites": {"id": "tlsv1_1", "name": "TLS 1.1", "is_insecure": False, "is_weak": True},
        "tls_1_2_cipher_suites": {"id": "tlsv1_2", "name": "TLS 1.2", "is_insecure": False, "is_weak": False},
        "tls_1_3_cipher_suites": {"id": "tlsv1_3", "name": "TLS 1.3", "is_insecure": False, "is_weak": False},
    }

    # Taken from https://ciphersuite.info/
    weak_ciphers = [
        "DHE-DSS-DES-CBC3-SHA",
        "DHE-DSS-AES128-SHA",
        "DHE-DSS-AES128-SHA256",
        "DHE-DSS-AES256-SHA",
        "DHE-DSS-AES256-SHA256",
        "DHE-DSS-CAMELLIA128-SHA",
        "DHE-DSS-CAMELLIA128-SHA256",
        "DHE-DSS-CAMELLIA256-SHA",
        "DHE-DSS-CAMELLIA256-SHA256",
        "DHE-DSS-SEED-SHA",
        "DHE-PSK-3DES-EDE-CBC-SHA",
        "DHE-PSK-AES128-CBC-SHA",
        "DHE-PSK-AES128-CBC-SHA256",
        "DHE-PSK-AES256-CBC-SHA",
        "DHE-PSK-AES256-CBC-SHA384",
        "DHE-PSK-CAMELLIA128-SHA256",
        "DHE-PSK-CAMELLIA256-SHA384",
        "DHE-RSA-DES-CBC3-SHA",
        "DHE-RSA-AES128-SHA",
        "DHE-RSA-AES128-SHA256",
        "DHE-RSA-AES256-SHA",
        "DHE-RSA-AES256-SHA256",
        "DHE-RSA-CAMELLIA128-SHA",
        "DHE-RSA-CAMELLIA128-SHA256",
        "DHE-RSA-CAMELLIA256-SHA",
        "DHE-RSA-CAMELLIA256-SHA256",
        "DHE-RSA-SEED-SHA",
        "ECDHE-ECDSA-DES-CBC3-SHA",
        "ECDHE-ECDSA-AES128-SHA",
        "ECDHE-ECDSA-AES128-SHA256",
        "ECDHE-ECDSA-AES256-SHA",
        "ECDHE-ECDSA-AES256-SHA384",
        "ECDHE-ECDSA-CAMELLIA128-SHA256",
        "ECDHE-ECDSA-CAMELLIA256-SHA384",
        "ECDHE-PSK-3DES-EDE-CBC-SHA",
        "ECDHE-PSK-AES128-CBC-SHA",
        "ECDHE-PSK-AES128-CBC-SHA256",
        "ECDHE-PSK-AES256-CBC-SHA",
        "ECDHE-PSK-AES256-CBC-SHA384",
        "ECDHE-PSK-CAMELLIA128-SHA256",
        "ECDHE-PSK-CAMELLIA256-SHA384",
        "ECDHE-RSA-DES-CBC3-SHA",
        "ECDHE-RSA-AES128-SHA",
        "ECDHE-RSA-AES128-SHA256",
        "ECDHE-RSA-AES256-SHA",
        "ECDHE-RSA-AES256-SHA384",
        "ECDHE-RSA-CAMELLIA128-SHA256",
        "ECDHE-RSA-CAMELLIA256-SHA384",
        "PSK-3DES-EDE-CBC-SHA",
        "PSK-AES128-CBC-SHA",
        "PSK-AES128-CBC-SHA256",
        "PSK-AES128-CCM",
        "PSK-AES128-CCM8",
        "PSK-AES128-GCM-SHA256",
        "PSK-AES256-CBC-SHA",
        "PSK-AES256-CBC-SHA384",
        "PSK-AES256-CCM",
        "PSK-AES256-CCM8",
        "PSK-AES256-GCM-SHA384",
        "PSK-CAMELLIA128-SHA256",
        "PSK-CAMELLIA256-SHA384",
        "PSK-CHACHA20-POLY1305",
        "RSA-PSK-3DES-EDE-CBC-SHA",
        "RSA-PSK-AES128-CBC-SHA",
        "RSA-PSK-AES128-CBC-SHA256",
        "RSA-PSK-AES128-GCM-SHA256",
        "RSA-PSK-AES256-CBC-SHA",
        "RSA-PSK-AES256-CBC-SHA384",
        "RSA-PSK-AES256-GCM-SHA384",
        "RSA-PSK-CAMELLIA128-SHA256",
        "RSA-PSK-CAMELLIA256-SHA384",
        "RSA-PSK-CHACHA20-POLY1305",
        "DES-CBC3-SHA",
        "AES128-SHA",
        "AES128-SHA256",
        "AES128-CCM",
        "AES128-CCM8",
        "AES128-GCM-SHA256",
        "AES256-SHA",
        "AES256-SHA256",
        "AES256-CCM",
        "AES256-CCM8",
        "AES256-GCM-SHA384",
        "CAMELLIA128-SHA",
        "CAMELLIA128-SHA256",
        "CAMELLIA256-SHA",
        "CAMELLIA256-SHA256",
        "IDEA-CBC-SHA",
        "SEED-SHA",
        "SRP-DSS-3DES-EDE-CBC-SHA",
        "SRP-DSS-AES-128-CBC-SHA",
        "SRP-DSS-AES-256-CBC-SHA",
        "SRP-RSA-3DES-EDE-CBC-SHA",
        "SRP-RSA-AES-128-CBC-SHA",
        "SRP-RSA-AES-256-CBC-SHA",
        "SRP-3DES-EDE-CBC-SHA",
        "SRP-AES-128-CBC-SHA",
        "SRP-AES-256-CBC-SHA",
    ]
    insecure_ciphers = [
        "ADH-DES-CBC3-SHA",
        "ADH-AES128-SHA",
        "ADH-AES128-SHA256",
        "ADH-AES128-GCM-SHA256",
        "ADH-AES256-SHA",
        "ADH-AES256-SHA256",
        "ADH-AES256-GCM-SHA384",
        "ADH-CAMELLIA128-SHA",
        "ADH-CAMELLIA128-SHA256",
        "ADH-CAMELLIA256-SHA",
        "ADH-CAMELLIA256-SHA256",
        "ADH-SEED-SHA",
        "DHE-PSK-NULL-SHA",
        "DHE-PSK-NULL-SHA256",
        "DHE-PSK-NULL-SHA384",
        "AECDH-DES-CBC3-SHA",
        "AECDH-AES128-SHA",
        "AECDH-AES256-SHA",
        "AECDH-NULL-SHA",
        "ECDHE-ECDSA-NULL-SHA",
        "ECDHE-PSK-NULL-SHA",
        "ECDHE-PSK-NULL-SHA256",
        "ECDHE-PSK-NULL-SHA384",
        "ECDHE-RSA-NULL-SHA",
        "PSK-NULL-SHA",
        "PSK-NULL-SHA256",
        "PSK-NULL-SHA384",
        "RSA-PSK-NULL-SHA",
        "RSA-PSK-NULL-SHA256",
        "RSA-PSK-NULL-SHA384",
        "NULL-MD5",
        "NULL-SHA",
        "NULL-SHA256",
    ]

    fallback_templates = [fallback_template(tags=f'scanimport:{id}:weak_tls_setup', translations=[
        FindingTemplateTranslation(
            language=Language.ENGLISH_US,
            title='Weak TLS setup might impact encryption',
            custom_fields={
                'cvss': "CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:C/C:L/I:L/A:N",
                'recommendation': "Update your TLS setup to protect your data in transit.",
                'references': [
                    "https://ssl-config.mozilla.org/",
                    "https://ciphersuite.info/",
                ],
                'summary': textwrap.dedent(
                    """\
                    <!--{% oneliner %}-->
                    We found that <!--{{ affected_components_short|first }}-->
                    <!--{% if affected_components_short|length == 2 %}-->
                    and <!--{{ affected_components_short|last }}-->
                    <!--{% elif affected_components_short|length > 2 %}-->
                    and <!--{{ affected_components_short|length|add:"-1"|safe }}--> other services
                    <!--{% endif %}-->
                    had a weak TLS setup. This might impact the confidentiality and integrity of your data in transit.
                    <!--{% endoneliner %}-->
                    """),
                'description': textwrap.dedent(
                    """\
                    <!--{% if has_cert_issues %}--><!--{% oneliner %}-->
                    The certificates of <!--{{ affected_components_short|first }}-->
                    <!--{% if affected_components_short|length == 2 %}-->
                    and <!--{{ affected_components_short|last }}-->
                    <!--{% elif affected_components_short|length > 2 %}-->
                    and <!--{{ affected_components_short|length|add:"-1"|safe }}--> other services
                    <!--{% endif %}-->
                    are untrusted by common browsers:
                    <!--{% endoneliner %}-->

                    <!--{% noemptylines %}-->
                    <!--{% for t in targets %}-->
                    <!--{% if t.has_cert_issues %}-->
                    <!--{% oneliner %}-->
                    * <!--{{ t.hostname }}-->:<!--{{ t.port }}-->
                    <!--{% if t.certinfo.certificate_untrusted and not t.certinfo.certificate_matches_hostname %}-->
                    (unmatching hostname; untrusted by <!--{{ t.certinfo.certificate_untrusted|join:", " }}-->)
                    <!--{% elif t.certinfo.certificate_untrusted %}-->
                    (untrusted by <!--{{ t.certinfo.certificate_untrusted|join:", " }}-->)
                    <!--{% elif not t.certinfo.certificate_matches_hostname %}-->
                    (unmatching hostname)
                    <!--{% endif %}-->
                    <!--{% endoneliner %}-->
                    <!--{% endif %}-->
                    <!--{% endfor %}-->
                    <!--{% endnoemptylines %}-->
                    <!--{% endif %}-->

                    
                    <!--{% if has_vulnerabilities %}-->
                    **Vulnerabilities**

                    <!--{% oneliner %}-->
                    <!--{{ affected_components_short|first }}-->
                    <!--{% if affected_components_short|length == 2 %}-->
                    and <!--{{ affected_components_short|last }}-->
                    <!--{% elif affected_components_short|length > 2 %}-->
                    and <!--{{ affected_components_short|length|add:"-1"|safe }}--> other services
                    <!--{% endif %}-->
                    used outdated TLS libraries. This results in the following vulnerabilities:
                    <!--{% endoneliner %}-->


                    <!--{% noemptylines %}-->
                    |      | Heartbleed | Robot Attack | OpenSSL CCS |
                    | :--- | :--------: | :----------: | :---------: |
                    <!--{% for t in targets %}-->
                    <!--{% oneliner %}-->
                    | <!--{{ t.hostname }}-->:<!--{{ t.port }}--> | 
                    <span style="color: <!--{{ t.vulnerabilities.heartbleed|yesno:"red,green" }}-->"><!--{{ t.vulnerabilities.heartbleed|yesno:"Vulnerable,OK" }}--></span> |
                    <span style="color: <!--{{ t.vulnerabilities.robot|yesno:"red,green" }}-->"><!--{{ t.vulnerabilities.robot|yesno:"Vulnerable,OK" }}--></span> |
                    <span style="color: <!--{{ t.vulnerabilities.openssl_ccs|yesno:"red,green" }}-->"><!--{{ t.vulnerabilities.openssl_ccs|yesno:"Vulnerable,OK" }}--></span> |
                    <!--{% endoneliner %}-->
                    <!--{% endfor %}-->
                    <!--{% endnoemptylines %}-->
                    <!--{% endif %}-->

                    
                    <!--{% if has_insecure_ciphers or has_insecure_protocols %}-->
                    **Insecure Ciphers and Protocols**

                    <!--{% oneliner %}-->
                    We
                    <!--{% if has_vulnerabilities %}-->also<!--{% endif %}-->
                    found out that
                    <!--{{ affected_components_short|first }}-->
                    <!--{% if affected_components_short|length == 2 %}-->
                    and <!--{{ affected_components_short|last }}-->
                    <!--{% elif affected_components_short|length > 2 %}-->
                    and <!--{{ affected_components_short|length|add:"-1"|safe }}--> other services
                    <!--{% endif %}-->
                    had insecure ciphers or protocols enabled:
                    <!--{% endoneliner %}-->

                    <!--{% noemptylines %}-->
                    |      | SSLv2 | SSLv3 | TLS 1.0 | TLS 1.1 | Weak Ciphers | Insecure Ciphers |
                    | :--- | :---: | :---: | :-----: | :-----: | :----------: | :--------------: |
                    <!--{% for t in targets %}-->
                    <!--{% oneliner %}-->
                    | <!--{{ t.hostname }}-->:<!--{{ t.port }}--> | 
                    <!--{% if 'sslv2' in t.protocol_ids %}--><span style="color: red">Yes</span><!--{% else %}--><span style="color: green">No</span><!--{% endif %}--> |
                    <!--{% if 'sslv3' in t.protocol_ids %}--><span style="color: red">Yes</span><!--{% else %}--><span style="color: green">No</span><!--{% endif %}--> |
                    <!--{% if 'tlsv1_0' in t.protocol_ids %}--><span style="color: orange">Yes</span><!--{% else %}--><span style="color: green">No</span><!--{% endif %}--> |
                    <!--{% if 'tlsv1_1' in t.protocol_ids %}--><span style="color: orange">Yes</span><!--{% else %}--><span style="color: green">No</span><!--{% endif %}--> |
                    <span style="color: <!--{{ t.has_weak_ciphers|yesno:"orange,green" }}-->"><!--{{ t.has_weak_ciphers|yesno:"Yes,No" }}--></span> |
                    <span style="color: <!--{{ t.has_insecure_ciphers|yesno:"red,green" }}-->"><!--{{ t.has_insecure_ciphers|yesno:"Yes,No" }}--></span> |
                    <!--{% endoneliner %}-->
                    <!--{% endfor %}-->
                    <!--{% endnoemptylines %}--><!--{% endif %}-->

                    
                    <!--{% if has_misconfigurations %}-->
                    **Misconfigurations**

                    <!--{% oneliner %}-->
                    <!--{% if has_vulnerabilities or has_insecure_ciphers or has_insecure_protocols %}-->
                    Additionally, we
                    <!--{% else %}-->
                    We
                    <!--{% endif %}-->
                    detected the following misconfigurations:
                    <!--{% endoneliner %}-->

                    <!--{% noemptylines %}-->
                    |      | TLS Compression | Downgrade (no SCSV fallback) | No Secure Renegotiation | Client Renegotiation |
                    | :--- | :-------------: | :--------------------------: | :---------------------: | :------------------: |
                    <!--{% for t in targets %}-->
                    <!--{% oneliner %}-->
                    | <!--{{ t.hostname }}-->:<!--{{ t.port }}--> | 
                    <span style="color: <!--{{ t.misconfigurations.compression|yesno:"red,green" }}-->"><!--{{ t.misconfigurations.compression|yesno:"Yes,No" }}--></span> |
                    <span style="color: <!--{{ t.misconfigurations.downgrade|yesno:"red,green" }}-->"><!--{{ t.misconfigurations.downgrade|yesno:"Yes,No" }}--></span> |
                    <span style="color: <!--{{ t.misconfigurations.no_secure_renegotiation|yesno:"red,green" }}-->"><!--{{ t.misconfigurations.no_secure_renegotiation|yesno:"Yes,No" }}--></span> |
                    <span style="color: <!--{{ t.misconfigurations.accepts_client_renegotiation|yesno:"red,green" }}-->"><!--{{ t.misconfigurations.accepts_client_renegotiation|yesno:"Yes,No" }}--></span> |
                    <!--{% endoneliner %}-->
                    <!--{% endfor %}-->
                    <!--{% endnoemptylines %}--><!--{% endif %}-->
                    """),
            },
        ),
    ])]

    def is_format(self, file):
        file.seek(0)
        data = json.load(file)
        return isinstance(data, dict) and 'sslyze_version' in data
    
    def get_protocols(self, scan_result):
        protocols = []
        for protocol, protocol_data in scan_result["scan_result"].items():
            if (protocol_data.get("result") or {}).get("accepted_cipher_suites"):
                if p_info := self.protocol_mapping.get(protocol):
                    protocols.append(p_info)

        protocols = sorted(protocols, key=lambda p: [m['id'] for m in self.protocol_mapping.values()].index(p['id']))
        return protocols
    
    def get_ciphers(self, scan_result):
        ciphers = []
        for protocol, protocol_data in scan_result["scan_result"].items():
            for c in (protocol_data.get("result") or {}).get("accepted_cipher_suites", []):
                c_name = c['cipher_suite']['openssl_name']
                ciphers.append({
                    'name': c_name,
                    'protocol': self.protocol_mapping.get(protocol, protocol),
                    'is_weak': c_name in self.weak_ciphers,
                    'is_insecure': c_name in self.insecure_ciphers,
                })
        ciphers = sorted(ciphers, key=lambda c: ([m['id'] for m in self.protocol_mapping.values()].index(c['protocol']['id']), c['is_insecure'] * -1, c['is_weak'] * -1))
        return ciphers
    
    def get_certinfo(self, scan_result):
        deployments = scan_result.get('scan_result', {}).get('certificate_info', {}).get('result', {}).get('certificate_deployments', [])
        path_validation_results = list(itertools.chain(*[d.get('path_validation_results', []) for d in deployments]))

        certinfo = {
            'certificate_matches_hostname': all(d.get('leaf_certificate_subject_matches_hostname', True) for d in deployments),
            'has_sha1_in_certificate_chain': any(d.get('verified_chain_has_sha1_signature', False) for d in deployments),
            'certificate_untrusted': [v.get('trust_store', {}).get('name') for v in path_validation_results if not v.get('was_validation_successful', True)],
        }
        certinfo['has_cert_issues'] = certinfo['certificate_untrusted'] or certinfo['has_sha1_in_certificate_chain'] or not certinfo['certificate_matches_hostname']
        return certinfo
    
    def get_vulnerabilities(self, scan_result):
        return {
            'heartbleed': scan_result.get('scan_result', {}).get('heartbleed', {}).get('result', {}).get('is_vulnerable_to_heartbleed', False),
            'openssl_ccs': scan_result.get('scan_result', {}).get('openssl_ccs_injection', {}).get('result', {}).get('is_vulnerable_to_ccs_injection', False),
            'robot': 'NOT_VULNERABLE' not in scan_result.get('scan_result', {}).get('robot', {}).get('result', {}).get('robot_result', 'NOT_VULNERABLE'),
        }
    
    def get_misconfigurations(self, scan_result):
        return {
            'compression': scan_result.get('scan_result', {}).get('tls_compression', {}).get('result', {}).get('supports_compression', False),
            'downgrade': not scan_result.get('scan_result', {}).get('tls_fallback_scsv', {}).get('result', {}).get('supports_fallback_scsv', True),
            'client_renegotiation': scan_result.get('scan_result', {}).get('session_renegotiation', {}).get('result', {}).get('is_vulnerable_to_client_renegotiation_dos', False),
            'no_secure_renegotiation': not scan_result.get('scan_result', {}).get('session_renegotiation', {}).get('result', {}).get('supports_secure_renegotiation', True),
        }

    def parse_sslyze_data(self, files):
        out = []
        for file in files:
            file.seek(0)
        
            for scan_result in json.load(file).get('server_scan_results', []):
                target_data = scan_result['server_location'] | {
                    'protocols': self.get_protocols(scan_result),
                    'ciphers': self.get_ciphers(scan_result),
                    'certinfo': self.get_certinfo(scan_result),
                    'vulnerabilities': self.get_vulnerabilities(scan_result),
                    'misconfigurations': self.get_misconfigurations(scan_result),
                }
                finding_flags = {
                    'has_weak_protocols': any(p['is_weak'] for p in target_data['protocols']),
                    'has_insecure_protocols': any(p['is_insecure'] for p in target_data['protocols']),
                    'has_weak_ciphers': any(c['is_weak'] for c in target_data['ciphers']),
                    'has_insecure_ciphers': any(c['is_insecure'] for c in target_data['ciphers']),
                    'has_cert_issues': target_data['certinfo']['has_cert_issues'],
                    'has_vulnerabilities': any(v for v in target_data['vulnerabilities'].values()),
                    'has_misconfigurations': any(v for v in target_data['misconfigurations'].values()),
                }
                target_data |= finding_flags | {
                    'flag_for_finding': any(finding_flags.values()),
                    'protocol_ids': [p['id'] for p in target_data['protocols']],
                }
                out.append(target_data)
        return out

    def parse_notes(self, files):
        notes = []

        note_root = ProjectNotebookPage(
            icon_emoji='🔒',
            title='Sslyze',
        )
        notes.append(note_root)

        for idx, target in enumerate(self.parse_sslyze_data(files)):
            notes.append(ProjectNotebookPage(
                parent=note_root,
                order=idx + 1,
                checked=False,
                title=f"{'🚩 ' if target['flag_for_finding'] else ''}{target['hostname']}:{target['port']} ({target['ip_address']})",
                text=render_template_string(textwrap.dedent(
                    """\
                    **Protocols**

                    <!--{% noemptylines %}-->
                    <!--{% for protocol in protocols %}-->
                    <!--{% if protocol.is_insecure %}-->
                    * <span style="color: red"><!--{{ protocol.name }}--></span>
                    <!--{% elif protocol.is_weak %}-->
                    * <span style="color: orange"><!--{{ protocol.name }}--></span>
                    <!--{% else %}-->
                    * <span style="color: green"><!--{{ protocol.name }}--></span>
                    <!--{% endif %}-->
                    <!--{% endfor %}-->
                    <!--{% endnoemptylines %}-->


                    **Certificate Information**

                    <!--{% noemptylines %}-->
                    <!--{% if certinfo.certificate_untrusted %}-->
                    * <span style="color: red">Certificate untrusted by:</span>
                    <!--{% for browser in certinfo.certificate_untrusted %}-->
                        * <!--{{ browser }}-->
                    <!--{% endfor %}-->
                    <!--{% else %}-->
                    * <span style="color: green">Certificate is trusted</span>
                    <!--{% endif %}-->
                    * Certificate matches hostname: <span style="color: <!--{% if certinfo.certificate_matches_hostname %}-->green<!--{% else %}-->red<!--{% endif %}-->"><!--{{ certinfo.certificate_matches_hostname|yesno:"Yes,No" }}--></span>
                    * SHA1 in certificate chain: <span style="color: <!--{% if certinfo.has_sha1_in_certificate_chain %}-->red<!--{% else %}-->green<!--{% endif %}-->"><!--{{ certinfo.has_sha1_in_certificate_chain|yesno:"Yes,No" }}--></span>
                    <!--{% endnoemptylines %}-->


                    **Vulnerabilities**

                    <!--{% noemptylines %}-->
                    * Heartbleed: <span style="color: <!--{{ vulnerabilities.heartbleed|yesno:"red,green" }}-->"><!--{{ vulnerabilities.heartbleed|yesno:"Yes,No" }}--></span>
                    * Robot Attack: <span style="color: <!--{{ vulnerabilities.robot|yesno:"red,green" }}-->"><!--{{ vulnerabilities.robot|yesno:"Yes,No" }}--></span>
                    * OpenSSL CCS (CVE-2014-0224): <span style="color: <!--{{ vulnerabilities.openssl_ccs|yesno:"red,green" }}-->"><!--{{ vulnerabilities.openssl_ccs|yesno:"Yes,No" }}--></span>
                    <!--{% endnoemptylines %}-->


                    **Misconfigurations**

                    <!--{% noemptylines %}-->
                    * Compression: <span style="color: <!--{% if misconfigurations.compression %}-->red<!--{% else %}-->green<!--{% endif %}-->"><!--{{ misconfigurations.compression|yesno:"Yes,No" }}--></span>
                    * Downgrade Attack (no SCSV fallback): <span style="color: <!--{% if misconfigurations.downgrade %}-->red<!--{% else %}-->green<!--{% endif %}-->"><!--{{ misconfigurations.downgrade|yesno:"Yes,No" }}--></span>
                    * No Secure Renegotiation: <span style="color: <!--{% if misconfigurations.no_secure_renegotiation %}-->red<!--{% else %}-->green<!--{% endif %}-->"><!--{{ misconfigurations.no_secure_renegotiation|yesno:"Yes,No" }}--></span>
                    * Client Renegotiation: <span style="color: <!--{% if misconfigurations.accepts_client_renegotiation %}-->red<!--{% else %}-->green<!--{% endif %}-->"><!--{{ misconfigurations.accepts_client_renegotiation|yesno:"Yes,No" }}--></span>
                    <!--{% endnoemptylines %}-->


                    **Weak Cipher Suites**

                    <!--{% noemptylines %}-->
                    <!--{% if not has_weak_ciphers and not has_insecure_ciphers %}-->
                    <span style="color: green">No weak ciphers found<!--{% else %}-->
                    <!--{% endif %}-->
                    <!--{% for cipher in ciphers %}-->
                    <!--{% if cipher.is_insecure %}-->
                    * <span style="color: red"><!--{{ cipher.name }}--></span> (<!--{{ cipher.protocol.name }}-->)
                    <!--{% elif cipher.is_weak %}-->
                    * <span style="color: orange"><!--{{ cipher.name }}--></span> (<!--{{ cipher.protocol.name }}-->)
                    <!--{% endif %}-->
                    <!--{% endfor %}-->
                    <!--{% endnoemptylines %}-->
                    """), context=target),
            ))

        return notes

    def parse_findings(self, files, project):
        targets = [t for t in self.parse_sslyze_data(files) if t.get('flag_for_finding')]
        if not targets:
            return []

        templates = self.get_all_finding_templates()
        return [self.generate_finding_from_template(
            tr=self.select_finding_template(
                templates=templates,
                fallback=self.fallback_templates,
                selector='weak_tls_setup',
                language=project.language,
            ),
            data={
                'targets': targets,
                'affected_components': [f"{t['hostname']}:{t['port']} ({t['ip_address']})" for t in targets],
                'affected_components_short': [f"{t['hostname']}:{t['port']}" for t in targets],
                'has_vulnerabilities': any(t.get('has_vulnerabilities') for t in targets),
                'has_misconfigurations': any(t.get('has_misconfigurations') for t in targets),
                'has_weak_protocols': any(t.get('has_weak_protocols') for t in targets),
                'has_insecure_protocols': any(t.get('has_insecure_protocols') for t in targets),
                'has_weak_ciphers': any(t.get('has_weak_ciphers') for t in targets),
                'has_insecure_ciphers': any(t.get('has_insecure_ciphers') for t in targets),
                'has_cert_issues': any(t.get('has_cert_issues') for t in targets),
            },
            project=project,
        )]