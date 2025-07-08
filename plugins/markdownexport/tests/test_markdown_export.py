import io
import zipfile

import pytest
from django.urls import reverse
from sysreptor.pentests.fielddefinition.predefined_fields import (
    FINDING_FIELDS_CORE,
    FINDING_FIELDS_PREDEFINED,
    REPORT_FIELDS_CORE,
)
from sysreptor.plugins import (
    DateField,
    FieldDefinition,
    ListField,
    MarkdownField,
    ObjectField,
    StringField,
)
from sysreptor.tests.mock import (
    api_client,
    create_project,
    create_project_type,
    create_user,
)
from sysreptor.utils.fielddefinition.types import serialize_field_definition

from ..apps import MarkdownExportPluginConfig
from ..md_format import format_project

MARKDOWNEXPORT_APPLABEL = MarkdownExportPluginConfig.label


@pytest.mark.django_db
class TestMarkdownFormatting:
    def test_markdown_formatting(self):
        pt = create_project_type(
            report_sections=[
                {
                    'id': 'meta',
                    'label': 'Meta',
                    'fields': serialize_field_definition(FieldDefinition(fields=[
                        *REPORT_FIELDS_CORE.fields,
                        DateField(id='report_date', label='Report Date', required=True),
                        StringField(id='pentester', label='Pentester', required=True),
                    ])),
                },
                {
                    'id': 'executive_summary',
                    'label': 'Executive Summary',
                    'fields': serialize_field_definition(FieldDefinition(fields=[
                        MarkdownField(id='executive_summary', label='Executive Summary'),
                    ])),
                },
                {
                    'id': 'field_types',
                    'label': 'Field Types',
                    'fields': [
                        {'id': 'field_string', 'type': 'string', 'label': 'String Field', 'default': 'test'},
                        {'id': 'field_markdown', 'type': 'markdown', 'label': 'Markdown Field', 'default': '# test\nmarkdown'},
                        {'id': 'field_cvss', 'type': 'cvss', 'label': 'CVSS Field', 'default': 'n/a'},
                        {'id': 'field_cwe', 'type': 'cwe', 'label': 'CWE Field', 'default': 'CWE-89'},
                        {'id': 'field_date', 'type': 'date', 'label': 'Date Field', 'default': '2022-01-01'},
                        {'id': 'field_int', 'type': 'number', 'label': 'Number Field', 'default': 10},
                        {'id': 'field_bool', 'type': 'boolean', 'label': 'Boolean Field', 'default': False},
                        {'id': 'field_enum', 'type': 'enum', 'label': 'Enum Field', 'choices': [{'value': 'enum1', 'label': 'Enum Value 1'}, {'value': 'enum2', 'label': 'Enum Value 2'}], 'default': 'enum2'},
                        {'id': 'field_combobox', 'type': 'combobox', 'label': 'Combobox Field', 'suggestions': ['value 1', 'value 2'], 'default': 'value1'},
                        {'id': 'field_list', 'type': 'list', 'label': 'List Field', 'items': {'type': 'string'}},
                    ],
                },
                {
                    'id': 'appendix',
                    'label': 'Appendix',
                    'fields': serialize_field_definition(FieldDefinition(fields=[
                        ListField(id='appendix', items=ObjectField(id='appendix_sections', label='Appendix Sections', properties=[
                            StringField(id='title', label='Title', required=True, default='Appendix Title'),
                            MarkdownField(id='content', label='Content', required=True),
                        ])),
                    ])),
                }
            ],
            finding_fields=serialize_field_definition(FieldDefinition(fields=[
                *FINDING_FIELDS_CORE.fields,
                *[FINDING_FIELDS_PREDEFINED[f] for f in ['cvss', 'description', 'recommendation', 'affected_components']],
            ])),
        )
        p = create_project(project_type=pt, report_data={
            'title': 'Project Title',
            'report_date': '2025-01-01',
            'pentester': 'John Doe',
            'executive_summary': 'This is the **executive summary** with _markdown_ text.\n\nAnd multiple paragraphs.',
            'appendix': [
                {'title': 'Appendix 1', 'content': 'This is the content of the appendix section with **bold** text.'},
                {'title': 'Appendix 2', 'content': 'This is another appendix section with _italic_ text.'},
            ],
            'field_string': 'This is a string field.',
            'field_markdown': 'This field supports **markdown** formatting.',
            'field_cvss': 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H',
            'field_cwe': 'CWE-89',
            'field_date': '2022-01-01',
            'field_int': 42,
            'field_bool': True,
            'field_enum': 'enum1',
            'field_combobox': 'value2',
            'field_list': ['item1', 'item2', 'item3'],
        }, findings_kwargs=[
            {'data': {
                'title': 'Finding 1',
                'cvss': 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H',
                'description': 'This is a **markdown** description with *italic* and **bold** text.',
                'recommendation': 'This is a recommendation with\n* bullet points.\n* Another point.',
                'affected_components': ['Component A', 'Component B'],
            }},
            {'data': {
                'title': 'Finding 2',
                'cvss': 'n/a',
                'description': 'description2',
                'recommendation': 'recommendation2',
                'affected_components': [],
            }},
        ])
        f1 = p.findings.order_by('created')[0]
        f2 = p.findings.order_by('created')[1]

        actual = format_project(p).strip()
        expected = f'''
        # {p.data['title']} {{#project-title}}

        ## Table of Contents {{#table-of-contents}}

        * [{p.data['title']}](#project-title)
            * [Table of Contents](#table-of-contents)
            * [Meta](#meta)
            * [Executive Summary](#executive-summary)
            * [Field Types](#field-types)
            * [Findings](#findings)
                * [{f1.data['title']}](#{f1.finding_id})
                * [{f2.data['title']}](#{f2.finding_id})
            * [Appendix](#appendix)
                * [{p.data['appendix'][0]['title']}](#appendix-1)
                * [{p.data['appendix'][1]['title']}](#appendix-2)

        ## Meta {{#meta}}

        ### Report Date

        {p.data['report_date']}

        ### Pentester

        {p.data['pentester']}

        
        ## Executive Summary {{#executive-summary}}

        {p.data['executive_summary']}

        
        ## Field Types {{#field-types}}

        ### String Field

        {p.data['field_string']}

        ### Markdown Field

        {p.data['field_markdown']}

        ### CVSS Field

        {p.data['field_cvss']} (9.8 - Critical)

        ### CWE Field

        {p.data['field_cwe']}

        ### Date Field

        {p.data['field_date']}

        ### Number Field

        {p.data['field_int']}

        ### Boolean Field

        {p.data['field_bool']}

        ### Enum Field

        Enum Value 1

        ### Combobox Field

        {p.data['field_combobox']}

        ### List Field

        * {p.data['field_list'][0]}
        * {p.data['field_list'][1]}
        * {p.data['field_list'][2]}

        
        ## Findings {{#findings}}

        ### {f1.data['title']} {{#{f1.finding_id}}}

        #### CVSS

        {f1.data['cvss']} (9.8 - Critical)

        #### Technical Description

        {f1.data['description']}

        #### Recommendation

        {f1.data['recommendation']}

        #### Affected Components

        * {f1.data['affected_components'][0]}
        * {f1.data['affected_components'][1]}


        ### {f2.data['title']} {{#{f2.finding_id}}}

        #### CVSS

        n/a (0.0 - Info)

        #### Technical Description

        description2

        #### Recommendation

        recommendation2

        #### Affected Components

        

        
        ## Appendix {{#appendix}}

        ### {p.data['appendix'][0]['title']} {{#appendix-1}}

        {p.data['appendix'][0]['content']}

        ### {p.data['appendix'][1]['title']} {{#appendix-2}}

        {p.data['appendix'][1]['content']}
        '''
        # Remove leading spaces from each line for comparison
        expected = '\n'.join(line[8:] if not line[:8].strip() else line for line in expected.splitlines()).strip()

        assert actual == expected


@pytest.mark.django_db()
class TestMarkdownExportApi:
    def test_api(self):
        u = create_user()
        p = create_project(
            members=[u],
            report_data={
                'field_markdown': '![image](/images/name/test.png)',
            }, 
            images_kwargs=[{'name': 'test.png'}, {'name': 'unused.png'}],
        )
        res = api_client(u).post(reverse(f'{MARKDOWNEXPORT_APPLABEL}:markdownexport', kwargs={'project_pk': p.id}))
        assert res.status_code == 200
        assert res['Content-Type'] == 'application/zip'
        content = b''.join(res.streaming_content)
        with zipfile.ZipFile(io.BytesIO(content), mode='r') as z:
            assert zipfile.Path(z, 'report.md').exists()
            assert zipfile.Path(z, 'assets/test.png').exists()
            assert not zipfile.Path(z, 'assets/unused.png').exists()

    def test_permissions(self):
        p = create_project()
        res = api_client(create_user()).post(reverse(f'{MARKDOWNEXPORT_APPLABEL}:markdownexport', kwargs={'project_pk': p.id}))
        assert res.status_code == 404
