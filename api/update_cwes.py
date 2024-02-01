import io
import requests
import zipfile
import json
from pathlib import Path
from lxml import etree


def download_cwe_xml():
    res = requests.get('https://cwe.mitre.org/data/xml/cwec_latest.xml.zip').content
    with zipfile.ZipFile(file=io.BytesIO(res)) as zip:
        return zip.read(zip.namelist()[0])


def main():
    cwes = []
    cwe_xml = etree.fromstring(download_cwe_xml())
    weaknesses_xml = cwe_xml.findall('./Weaknesses/Weakness', namespaces=cwe_xml.nsmap)
    for w in weaknesses_xml:
        if w.attrib['Status'] == 'Deprecated':
            continue
        parent_ref = w.find('./Related_Weaknesses/Related_Weakness[@Nature="ChildOf"][@Ordinal="Primary"][@View_ID="1000"][@CWE_ID]', namespaces=cwe_xml.nsmap)
        cwes.append({
            'id': int(w.attrib['ID']),
            'name': w.attrib['Name'],
            'description': w.find('./Description', namespaces=cwe_xml.nsmap).text,
            'parent': int(parent_ref.attrib['CWE_ID']) if parent_ref is not None else None,
        })

    cwes = sorted(cwes, key=lambda cwe: cwe['id'])
    out_path = Path(__file__).parent / 'src/reportcreator_api/pentests/customfields/cwe.json'
    out_path.write_text(json.dumps(cwes, indent=2))



if __name__ == '__main__':
    main()
