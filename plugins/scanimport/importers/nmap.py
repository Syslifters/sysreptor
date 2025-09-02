import ipaddress
import textwrap

from lxml import etree
from sysreptor.pentests.models import (
    ProjectNotebookPage,
)
from sysreptor.utils.utils import groupby_to_dict

from ..utils import parse_xml, render_template_string
from .base import BaseImporter


class NmapImporter(BaseImporter):
    id = 'nmap'

    def is_format(self, file):
        try:
            return bool(parse_xml(file).xpath('/nmaprun/host'))
        except etree.XMLSyntaxError:
            file.seek(0)
            try:
                if not file.read(100).startswith(b'# Nmap'):
                    return False
                self.parse_nmap_greppable(file)
                return True
            except Exception:
                return False

    def parse_nmap_xml(self, file):
        ports = []
        for host in parse_xml(file).xpath('/nmaprun/host'):
            ip = host.xpath('address[@addrtype="ipv4" or @addrtype="ipv6"]/@addr')
            hostname = host.xpath('hostnames/hostname/@name')
            for port in host.xpath('ports/port'):
                state = port.xpath('state/@state')
                service = port.xpath('service')
                if state and state[0] == 'open':
                    ports.append({
                        'ip': ipaddress.ip_address(ip[0]) if ip else ipaddress.ip_address('0.0.0.0'),
                        'hostname': hostname[0] if hostname else None,
                        'port': port.attrib.get('portid'),
                        'protocol': port.attrib.get('protocol'),
                        'service': service[0].attrib.get('name') if service else None,
                        'version': service[0].attrib.get('product') if service else None,
                    })
        return ports
    
    def parse_nmap_greppable(self, file):
        out = []
        file.seek(0)
        for line in file.read().decode().splitlines():
            if line.startswith("#") or "Ports:" not in line:
                continue
            ip, ports = line.split("Ports:")
            ip = ip.split(" ")[1]

            for port in ports.split(','):
                port, status, protocol, _, service, _, version, _ = port.strip().split("/")
                if status == 'open':
                    out.append({
                        'ip': ipaddress.ip_address(ip),
                        'hostname': None,  # No hostname in greppable format
                        'port': port,
                        'protocol': protocol,
                        'service': service,
                        'version': version
                    })
        return out

    def parse_nmap_data(self, files):
        ports = []
        for file in files:
            try:
                ports.extend(self.parse_nmap_xml(file))
            except etree.XMLSyntaxError:
                ports.extend(self.parse_nmap_greppable(file))
        return ports

    def parse_notes(self, files):
        notes = []

        data = self.parse_nmap_data(files)
        nmap_table_template = textwrap.dedent("""\
        <!--{% noemptylines %}-->
        <!--{% if show_hostname %}-->

        | Hostname | IP | Port | Service | Version |
        | ------- | ------- | ------- | ------- | ------- |
        <!--{% for service in data %}-->| <!--{{service.hostname}}--> | <!--{{service.ip}}--> | <!--{{service.port}}-->/<!--{{service.protocol}}--> | <!--{{service.service|default:"n/a"}}--> | <!--{{service.version|default:"n/a"}}--> |
        <!--{% endfor %}-->

        <!--{% else %}-->

        | Host | Port | Service | Version |
        | ------- | ------- | ------- | ------- |
        <!--{% for service in data %}-->| <!--{{service.ip}}--> | <!--{{service.port}}-->/<!--{{service.protocol}}--> | <!--{{ service.service|default:"n/a"}}--> | <!--{{service.version|default:"n/a"}}--> |
        <!--{% endfor %}-->
        <!--{% endif %}-->

        <!--{% endnoemptylines %}-->
        """)

        note_root = ProjectNotebookPage(
            icon_emoji='👁️‍🗨️',
            title='Nmap',
            text=render_template_string(nmap_table_template, {
                'data': data, 
                'show_hostname': any(s.get('hostname') for s in data),
            }),
        )
        notes.append(note_root)

        order = 0
        for ip, ip_data in groupby_to_dict(data, key=lambda f: f['ip']).items():
            order += 1
            note_host = ProjectNotebookPage(
                parent=note_root,
                order=order,
                checked=False,
                title=ip,
                text=render_template_string(nmap_table_template, {
                    'data': ip_data,
                    'show_hostname': any(s.get('hostname') for s in ip_data),
                }),
            )
            notes.append(note_host)
        return notes
