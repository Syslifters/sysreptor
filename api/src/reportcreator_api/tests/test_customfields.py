import copy
import itertools
from datetime import timedelta
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from reportcreator_api.pentests.collab.text_transformations import SelectionRange
from reportcreator_api.pentests.customfields.mixins import CustomFieldsMixin
from reportcreator_api.pentests.customfields.predefined_fields import (
    FINDING_FIELDS_CORE,
    FINDING_FIELDS_PREDEFINED,
    REPORT_FIELDS_CORE,
    finding_fields_default,
    report_fields_default,
)
from reportcreator_api.pentests.customfields.sort import sort_findings
from reportcreator_api.pentests.customfields.types import (
    FieldDataType,
    field_definition_to_dict,
    parse_field_definition,
)
from reportcreator_api.pentests.customfields.utils import (
    HandleUndefinedFieldsOptions,
    check_definitions_compatible,
    ensure_defined_structure,
)
from reportcreator_api.pentests.customfields.validators import FieldDefinitionValidator, FieldValuesValidator
from reportcreator_api.pentests.models import FindingTemplate, FindingTemplateTranslation, Language
from reportcreator_api.pentests.models.project import Comment
from reportcreator_api.tasks.rendering.entry import format_template_field_object
from reportcreator_api.tests.mock import (
    create_comment,
    create_finding,
    create_project,
    create_project_type,
    create_template,
    create_user,
)
from reportcreator_api.tests.utils import assertKeysEqual
from reportcreator_api.utils.utils import copy_keys, omit_items, omit_keys


@pytest.mark.parametrize(('valid', 'definition'), [
    (True, {}),
    (False, {'f': {}}),
    (False, {'f': {'type': 'string'}}),
    # Test field id
    (True, {'field1': {'type': 'string', 'label': 'Field 1', 'default': None}}),
    (True, {'fieldNumber_one': {'type': 'string', 'label': 'Field 1', 'default': None}}),
    (False, {'field 1': {'type': 'string', 'label': 'Field 1', 'default': None}}),
    (False, {'field.one': {'type': 'string', 'label': 'Field 1', 'default': None}}),
    (False, {'1st_field': {'type': 'string', 'label': 'Field 1', 'default': None}}),
    # Test data types
    (True, {
        'field_string': {'type': 'string', 'label': 'String Field', 'default': 'test'},
        'field_markdown': {'type': 'markdown', 'label': 'Markdown Field', 'default': '# test\nmarkdown'},
        'field_cvss': {'type': 'cvss', 'label': 'CVSS Field', 'default': 'n/a'},
        'field_cwe': {'type': 'cwe', 'label': 'CWE Field', 'default': 'CWE-89'},
        'field_date': {'type': 'date', 'label': 'Date Field', 'default': '2022-01-01'},
        'field_int': {'type': 'number', 'label': 'Number Field', 'default': 10},
        'field_bool': {'type': 'boolean', 'label': 'Boolean Field', 'default': False},
        'field_enum': {'type': 'enum', 'label': 'Enum Field', 'choices': [{'value': 'enum1', 'label': 'Enum Value 1'}, {'value': 'enum2', 'label': 'Enum Value 2'}], 'default': 'enum2'},
        'field_combobox': {'type': 'combobox', 'label': 'Combobox Field', 'suggestions': ['value 1', 'value 2'], 'default': 'value1'},
        'field_user': {'type': 'user', 'label': 'User Field'},
        'field_object': {'type': 'object', 'label': 'Nested Object', 'properties': {'nested1':  {'type': 'string', 'label': 'Nested Field'}}},
        'field_list': {'type': 'list', 'label': 'List Field', 'items': {'type': 'string'}},
        'field_list_objects': {'type': 'list', 'label': 'List of nested objects', 'items': {'type': 'object', 'properties': {'nested1': {'type': 'string', 'label': 'Nested object field', 'default': None}}}},
    }),
    (False, {'f': {'type': 'unknown', 'label': 'Unknown'}}),
    (False, {'f': {'type': 'date', 'label': 'Date', 'default': 'not a date'}}),
    (False, {'f': {'type': 'number', 'label': 'Number', 'default': 'not an int'}}),
    (False, {'f': {'type': 'enum', 'label': 'Enum Filed'}}),
    (False, {'f': {'type': 'enum', 'label': 'Enum Field', 'choices': []}}),
    (False, {'f': {'type': 'enum', 'label': 'Enum Field', 'choices': [{'value': 'v1'}]}}),
    (False, {'f': {'type': 'enum', 'label': 'Enum Field', 'choices': [{'value': None}]}}),
    (False, {'f': {'type': 'enum', 'label': 'Enum Field', 'choices': [{'label': 'Name only'}]}}),
    (False, {'f': {'type': 'cwe', 'label': 'CWE Field', 'default': 'not a CWE'}}),
    (False, {'f': {'type': 'combobox'}}),
    (False, {'f': {'type': 'combobox', 'suggestions': [None]}}),
    (False, {'f': {'type': 'object', 'label': 'Object Field'}}),
    (False, {'f': {'type': 'object', 'label': 'Object Field', 'properties': {'adsf': {}}}}),
    (False, {'f': {'type': 'list', 'label': 'List Field'}}),
    (False, {'f': {'type': 'list', 'label': 'List Field', 'items': {}}}),
])
def test_definition_formats(valid, definition):
    res_valid = True
    try:
        FieldDefinitionValidator()(definition)
    except ValidationError:
        res_valid = False
    assert res_valid == valid


@pytest.mark.parametrize(('valid', 'definition', 'value'), [
    (True, {
            'field_string': {'type': 'string', 'label': 'String Field', 'default': 'test'},
            'field_string2': {'type': 'string', 'label': 'String Field', 'default': None},
            'field_markdown': {'type': 'markdown', 'label': 'Markdown Field', 'default': '# test\nmarkdown'},
            'field_cvss': {'type': 'cvss', 'label': 'CVSS Field', 'default': 'n/a'},
            'field_cwe': {'type': 'cwe', 'label': 'CWE Field', 'default': None},
            'field_date': {'type': 'date', 'label': 'Date Field', 'default': '2022-01-01'},
            'field_int': {'type': 'number', 'label': 'Number Field', 'default': 10},
            'field_bool': {'type': 'boolean', 'label': 'Boolean Field', 'default': False},
            'field_enum': {'type': 'enum', 'label': 'Enum Field', 'choices': [{'value': 'enum1', 'label': 'Enum Value 1'}, {'value': 'enum2', 'label': 'Enum Value 2'}], 'default': 'enum2'},
            'field_combobox': {'type': 'combobox', 'lable': 'Combobox Field', 'suggestions': ['a', 'b']},
            'field_object': {'type': 'object', 'label': 'Nested Object', 'properties': {'nested1':  {'type': 'string', 'label': 'Nested Field'}}},
            'field_list': {'type': 'list', 'label': 'List Field', 'items': {'type': 'string'}},
            'field_list_objects': {'type': 'list', 'label': 'List of nested objects', 'items': {'type': 'object', 'properties': {'nested1': {'type': 'string', 'label': 'Nested object field', 'default': None}}}},
        }, {
            'field_string': 'This is a string',
            'field_string2': None,
            'field_markdown': 'Some **markdown**\n* String\n*List',
            'field_cvss': 'CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:C/C:H/I:H/A:H',
            'field_cwe': 'CWE-89',
            'field_date': '2022-01-01',
            'field_int': 17,
            'field_bool': True,
            'field_enum': 'enum2',
            'field_combobox': 'value2',
            'field_object': {'nested1': 'val'},
            'field_list': ['test'],
            'field_list_objects': [{'nested1': 'test'}, {'nested1': 'values'}],
            'field_additional': 'test',
        }),
    (False, {'f': {'type': 'string'}}, {'f': {}}),
    (False, {'f': {'type': 'string'}}, {}),
    (False, {'f': {'type': 'cwe'}}, {'f': 'not a CWE'}),
    (False, {'f': {'type': 'cwe'}}, {'f': 'CWE-99999999'}),
    (False, {'f': {'type': 'list', 'items': {'type': 'object', 'properties': {'f': {'type': 'string'}}}}}, {'f': [{'f': 'v'}, {'f': 1}]}),
    (True, {'f': {'type': 'list', 'items': {'type': 'object', 'properties': {'f': {'type': 'string'}}}}}, {'f': [{'f': 'v'}, {'f': None}]}),
    (True, {'f': {'type': 'list', 'items': {'type': 'string'}}}, {'f': []}),
    (False, {'f': {'type': 'list', 'items': {'type': 'string'}}}, {'f': None}),
    (True, {'f': {'type': 'combobox', 'suggestions': ['a', 'b']}}, {'f': 'other'}),
    # (False, {'f': {'type': 'user'}}, {'f': str(uuid4())}),
])
def test_field_values(valid, definition, value):
    res_valid = True
    try:
        FieldValuesValidator(parse_field_definition(definition))(value)
    except (ValidationError, ValueError):
        res_valid = False
    assert res_valid == valid


@pytest.mark.django_db()
def test_user_field_value():
    user = create_user()
    FieldValuesValidator(parse_field_definition({'field_user': {'type': 'user', 'label': 'User Field'}}))({'field_user': str(user.id)})


class CustomFieldsTestModel(CustomFieldsMixin):
    def __init__(self, field_definition, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._field_definition = parse_field_definition(field_definition)

    @property
    def field_definition(self):
        return self._field_definition


@pytest.mark.parametrize(('definition', 'old_value', 'new_value'), [
    ({'a': {'type': 'string'}}, {'a': 'old'}, {'a': 'new'}),
    ({'a': {'type': 'string'}}, {'a': 'text'}, {'a': None}),
    ({'a': {'type': 'number'}}, {'a': 10}, {'a': None}),
    ({'a': {'type': 'enum', 'choices': [{'value': 'a'}]}}, {'a': 'a'}, {'a': None}),
    ({'a': {'type': 'list', 'items': {'type': 'enum', 'choices': [{'value': 'a'}]}}}, {'a': ['a', 'a']}, {'a': ['a', None]}),
    ({'a': {'type': 'list', 'items': {'type': 'string'}}}, {'a': ['text']}, {'a': []}),
])
def test_update_field_values(definition, old_value, new_value):
    m = CustomFieldsTestModel(field_definition=definition, custom_fields=old_value)
    m.update_data(new_value)
    assert m.data == new_value


@pytest.mark.parametrize(('compatible', 'a', 'b'), [
    (True, {'a': {'type': 'string'}}, {'b': {'type': 'string'}}),
    (True, {'a': {'type': 'string'}}, {'a': {'type': 'string'}}),
    (True, {'a': {'type': 'string', 'label': 'left', 'default': 'left', 'required': False}}, {'a': {'type': 'string', 'label': 'right', 'default': 'right', 'required': True}}),
    (True, {'a': {'type': 'string'}}, {'a': {'type': 'string'}, 'b': {'type': 'string'}}),
    (True, {'a': {'type': 'string'}, 'b': {'type': 'string'}}, {'a': {'type': 'string'}}),
    (False, {'a': {'type': 'string'}}, {'a': {'type': 'list', 'items': {'type': 'string'}}}),
    (False, {'a': {'type': 'string'}}, {'a': {'type': 'markdown'}}),
    (True, {'a': {'type': 'list', 'items': {'type': 'string'}}}, {'a': {'type': 'list', 'items': {'type': 'string'}}}),
    (False, {'a': {'type': 'list', 'items': {'type': 'string'}}}, {'a': {'type': 'list', 'items': {'type': 'number'}}}),
    (True, {'a': {'type': 'object', 'properties': {'a': {'type': 'string'}}}}, {'a': {'type': 'object', 'properties': {'a': {'type': 'string'}}}}),
    (True, {'a': {'type': 'object', 'properties': {'a': {'type': 'string'}}}}, {'a': {'type': 'object', 'properties': {'a': {'type': 'boolean'}}}}),
    (True, {'a': {'type': 'enum', 'choices': [{'value': 'a'}]}}, {'a': {'type': 'enum', 'choices': [{'value': 'a'}]}}),
    (True, {'a': {'type': 'enum', 'choices': [{'value': 'a'}]}}, {'a': {'type': 'enum', 'choices': [{'value': 'a'}, {'value': 'b'}]}}),
    (False, {'a': {'type': 'enum', 'choices': [{'value': 'a'}, {'value': 'b'}]}}, {'a': {'type': 'enum', 'choices': [{'value': 'a'}]}}),
    (True, {'a': {'type': 'combobox', 'suggestions': ['a']}}, {'a': {'type': 'combobox', 'choices': ['b']}}),
])
def test_definitions_compatible(compatible, a, b):
    assert check_definitions_compatible(parse_field_definition(a), parse_field_definition(b))[0] == compatible


@pytest.mark.django_db()
class TestUpdateFieldDefinition:
    @pytest.fixture(autouse=True)
    def setUp(self) -> None:
        self.project_type = create_project_type()
        self.project = create_project(project_type=self.project_type, findings_kwargs=[{}])
        self.finding = self.project.findings.first()

        self.project_other = create_project(findings_kwargs=[{}])
        self.finding_other = self.project_other.findings.first()

    def refresh_data(self):
        self.project_type.refresh_from_db()
        self.project.refresh_from_db()
        self.finding.refresh_from_db()
        self.project_other.refresh_from_db()
        self.finding_other.refresh_from_db()

    def test_add_report_field(self):
        default_value = 'new'
        self.project_type.report_fields |= {
            'field_new': {'type': 'string', 'label': 'New field', 'default': default_value},
        }
        self.project_type.save()
        self.refresh_data()

        section = self.project.sections.get(section_id='other')
        assert 'field_new' in section.section_definition['fields']
        assert self.project_type.report_preview_data['report']['field_new'] == default_value

        # New field added to projects
        assert 'field_new' in section.data
        assert section.data['field_new'] == default_value

        assert 'field_new' not in self.project_other.data_all

    def test_add_finding_field(self):
        default_value = 'new'
        self.project_type.finding_fields |= {
            'field_new': {'type': 'string', 'label': 'New field', 'default': default_value},
        }
        self.project_type.save()
        self.refresh_data()

        assert self.project_type.finding_field_order[-1] == 'field_new'
        assert self.project_type.report_preview_data['findings'][0]['field_new'] == default_value

        # New field added to projects
        assert 'field_new' in self.finding.data
        assert self.finding.data['field_new'] == default_value

        assert 'field_new' not in self.finding_other.data

    def test_delete_report_field(self):
        old_value = self.project.data['field_string']
        del self.project_type.report_fields['field_string']
        self.project_type.save()
        self.refresh_data()

        assert 'field_string' not in set(itertools.chain(*map(lambda s: s['fields'], self.project_type.report_sections)))
        assert 'field_string' in self.project_type.report_preview_data['report']

        # Field removed from project (but data is kept in DB)
        assert 'field_string' not in self.project.data
        assert 'field_string' in self.project.data_all
        assert self.project.data_all['field_string'] == old_value

        assert 'field_string' in self.project_other.data

    def test_delete_finding_field(self):
        old_value = self.finding.data['field_string']
        del self.project_type.finding_fields['field_string']
        self.project_type.save()
        self.refresh_data()

        assert 'field_string' not in self.project_type.finding_field_order
        assert 'field_string' in self.project_type.report_preview_data['findings'][0]

        # Field remove from project (but data is kept in DB)
        assert 'field_string' not in self.finding.data
        assert 'field_string' in self.finding.data_all
        assert self.finding.data_all['field_string'] == old_value

        assert 'field_string' in self.finding_other.data

    def test_change_type_report_field(self):
        self.project_type.report_fields |= {
            'field_string': {'type': 'object', 'label': 'Changed type', 'properties': {'nested': {'type': 'string', 'label': 'Nested field', 'default': 'default'}}},
        }
        self.project_type.save()
        self.refresh_data()

        assert isinstance(self.project_type.report_preview_data['report']['field_string'], dict)
        section = self.project.sections.get(section_id='other')
        assert section.data['field_string'] == {'nested': 'default'}

    def test_change_type_finding_field(self):
        self.project_type.finding_fields |= {
            'field_string': {'type': 'object', 'label': 'Changed type', 'properties': {'nested': {'type': 'string', 'label': 'Nested field', 'default': 'default'}}},
        }
        self.project_type.save()
        self.refresh_data()

        assert isinstance(self.project_type.report_preview_data['findings'][0]['field_string'], dict)
        assert self.finding.data['field_string'] == {'nested': 'default'}

    def test_change_default_report_field(self):
        default_val = 'changed'
        report_fields = copy.deepcopy(self.project_type.report_fields)
        report_fields['field_string']['default'] = default_val
        self.project_type.report_fields = report_fields
        self.project_type.save()
        self.refresh_data()

        assert self.project_type.report_preview_data['report']['field_string'] == default_val

        assert self.project.data['field_string'] != default_val

        project_new = create_project(project_type=self.project_type)
        assert project_new.data['field_string'] == default_val

    def test_change_default_finding_field(self):
        default_val = 'changed'
        finding_fields = copy.deepcopy(self.project_type.finding_fields)
        finding_fields['field_string']['default'] = default_val
        self.project_type.finding_fields = finding_fields
        self.project_type.save()
        self.refresh_data()

        for f in self.project_type.report_preview_data['findings']:
            assert f['field_string'] == default_val

        assert self.finding.data['field_string'] != default_val

        finding_new = create_finding(project=self.project)
        assert finding_new.data['field_string'] == default_val

    def test_restore_data_report_field(self):
        old_value = self.project.data['field_string']
        old_definition = self.project_type.report_fields['field_string']

        # Delete field from definition
        self.project_type.report_fields = omit_keys(self.project_type.report_fields, ['field_string'])
        self.project_type.save()
        self.refresh_data()
        assert 'field_string' not in self.project.data
        assert self.project.data_all['field_string'] == old_value

        # Restore field in definition
        self.project_type.report_fields |= {'field_string': old_definition | {'labal': 'Changed name', 'default': 'other'}}
        self.project_type.save()
        self.refresh_data()
        assert self.project.data['field_string'] == old_value

    def test_restore_data_finding_field(self):
        old_value = self.finding.data['field_string']
        old_definition = self.project_type.finding_fields['field_string']

        # Delete field from definition
        del self.project_type.finding_fields['field_string']
        self.project_type.save()
        self.refresh_data()
        assert 'field_string' not in self.finding.data
        assert self.finding.data_all['field_string'] == old_value

        # Restore field in definition
        self.project_type.finding_fields |= {'field_string': old_definition | {'labal': 'Changed name', 'default': 'other'}}
        self.project_type.save()
        self.refresh_data()
        assert self.finding.data['field_string'] == old_value

    def test_change_project_type_report_fields(self):
        old_value = self.project.data['field_string']
        project_type_new = create_project_type(report_fields=field_definition_to_dict(REPORT_FIELDS_CORE) | {
            'field_new': {'type': 'string', 'default': 'default', 'label': 'New field'},
        })
        self.project.project_type = project_type_new
        self.project.save()
        self.refresh_data()

        assert 'field_string' not in self.project.data
        assert self.project.data_all['field_string'] == old_value
        assert self.project.data['field_new'] == 'default'

    def test_change_project_type_finding_fields(self):
        old_value = self.project.data['field_string']
        project_type_new = create_project_type(finding_fields=field_definition_to_dict(FINDING_FIELDS_CORE) | {
            'field_new': {'type': 'string', 'default': 'default', 'label': 'New field'},
        })
        self.project.project_type = project_type_new
        self.project.save()
        self.refresh_data()

        assert 'field_string' not in self.finding.data
        assert self.finding.data_all['field_string'], old_value
        assert self.finding.data['field_new'], 'default'

    def test_change_default_report_field_sync_previewdata(self):
        # If preview_data == default => update to new default value
        default_val = 'default changed'
        report_fields = copy.deepcopy(self.project_type.report_fields)
        report_fields['field_string']['default'] = default_val
        self.project_type.report_fields = report_fields
        self.project_type.save()
        self.refresh_data()
        assert self.project_type.report_preview_data['report']['field_string'] == default_val

        # If preview_data != default => do not update
        preview_data_value = 'non-default value'
        self.project_type.report_preview_data['report']['field_string'] = preview_data_value
        report_fields['field_string']['default'] = 'default changed 2'
        self.project_type.report_fields = report_fields
        self.project_type.save()
        assert self.project_type.report_preview_data['report']['field_string'] == preview_data_value


@pytest.mark.django_db()
class TestUpdateFieldDefinitionSyncComments:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.project_type = create_project_type()
        initial_data = ensure_defined_structure({
            'field_markdown': 'Example text',
            'field_cvss': 'n/a',
            'field_list': ['item'],
            'field_object': {'field_string': 'Example text'},
            'field_list_objects': [{'field_markdown': 'Example text'}],
        }, definition=self.project_type.finding_fields_obj, handle_undefined=HandleUndefinedFieldsOptions.FILL_DEFAULT)
        self.project = create_project(project_type=self.project_type, report_data=initial_data, findings_kwargs=[{'data': initial_data}], comments=False)
        self.finding = self.project.findings.first()
        self.section = self.project.sections.get(section_id='other')

        self.comment_paths = ['field_markdown', 'field_cvss', 'field_list.[0]', 'field_object.field_string', 'field_list_objects.[0].field_markdown']
        for p in self.comment_paths:
            create_comment(finding=self.finding, path=p, text_position=SelectionRange(anchor=0, head=10) if 'field_markdown' in p else None)
            create_comment(section=self.section, path=p, text_position=SelectionRange(anchor=0, head=10) if 'field_markdown' in p else None)

    def test_update_projecttype_delete_fields(self):
        self.project_type.finding_fields = finding_fields_default()
        self.project_type.report_fields = report_fields_default()
        self.project_type.save()

        assert Comment.objects.filter_project(self.project).count() == 0

    def test_change_projecttype_delete_fields(self):
        pt2 = create_project_type()
        pt2.finding_fields = finding_fields_default()
        pt2.report_fields = report_fields_default()
        pt2.save()
        self.project.project_type = pt2
        self.project.save()

        assert Comment.objects.filter_project(self.project).count() == 0

    def test_fields_deleted(self):
        self.project_type.finding_fields = copy.deepcopy(self.project_type.finding_fields)
        self.project_type.report_fields = copy.deepcopy(self.project_type.report_fields)
        for d in [self.project_type.finding_fields, self.project_type.report_fields]:
            d['field_markdown_renamed'] = d.pop('field_markdown')
            del d['field_cvss']
            del d['field_object']['properties']['field_string']
            del d['field_list_objects']['items']['properties']['field_markdown']
            d['field_list']['type'] = 'string'
        self.project_type.save()

        assert Comment.objects.filter_project(self.project).count() == 0

    def test_field_added(self):
        self.project_type.finding_fields = self.project_type.finding_fields | {'field_new': {'type': 'string'}}
        self.project_type.report_fields = self.project_type.report_fields | {'field_new': {'type': 'string'}}
        self.project_type.save()

        # No comment deleted or created
        assert Comment.objects.filter_project(self.project).count() == len(self.comment_paths) * 2

    def test_field_moved_to_other_section(self):
        fields_moved = ['field_markdown', 'field_list', 'field_list_objects']
        rs = copy.deepcopy(self.project_type.report_sections)
        rs_other = next(s for s in rs if s['id'] == 'other')
        rs_other['fields'] = omit_items(rs_other['fields'], fields_moved)
        rs.append({'id': 'new', 'fields': fields_moved})
        self.project_type.report_sections = rs
        self.project_type.save()

        for cp in self.comment_paths:
            c = Comment.objects.filter_project(self.project).filter(path=cp).first()
            assert c.section.section_id == 'new' if cp.split('.')[0] in fields_moved else 'other'

    def test_type_changed_text_position_cleared(self):
        comments = list(Comment.objects.filter_project(self.project).filter(path='field_markdown'))

        self.project_type.finding_fields = copy.deepcopy(self.project_type.finding_fields)
        self.project_type.finding_fields['field_markdown']['type'] = 'cvss'
        self.project_type.report_fields = copy.deepcopy(self.project_type.report_fields)
        self.project_type.report_fields['field_markdown']['type'] = 'cvss'
        self.project_type.save()

        for c in comments:
            text_original = c.text_original
            c.refresh_from_db()
            assert c.text_position is None
            assert c.text_original == text_original


@pytest.mark.django_db()
class TestPredefinedFields:
    @pytest.fixture(autouse=True)
    def setUp(self) -> None:
        self.project_type = create_project_type(
            finding_fields=field_definition_to_dict(FINDING_FIELDS_CORE | copy_keys(FINDING_FIELDS_PREDEFINED, 'description')))
        project = create_project(project_type=self.project_type)
        self.finding = create_finding(project=project)

    def test_change_structure(self):
        self.project_type.finding_fields |= {
            'description': {'type': 'list', 'label': 'Changed', 'items': {'type': 'string', 'default': 'changed'}},
        }
        with pytest.raises(ValidationError):
            self.project_type.clean_fields()

    def test_add_conflicting_field(self):
        self.project_type.finding_fields |= {
            'recommendation': {'type': 'list', 'label': 'Changed', 'items': {'type': 'string', 'default': 'changed'}},
        }
        with pytest.raises(ValidationError):
            self.project_type.clean_fields()


@pytest.mark.django_db()
class TestTemplateFieldDefinition:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.project_type1 = create_project_type(
            finding_fields=field_definition_to_dict(FINDING_FIELDS_CORE | {
                'field1': {'type': 'string', 'default': 'default', 'label': 'Field 1'},
                'field_conflict': {'type': 'string', 'default': 'default', 'label': 'Conflicting field type'},
            }),
        )
        self.project_type2 = create_project_type(
            finding_fields=field_definition_to_dict(FINDING_FIELDS_CORE | {
                'field2': {'type': 'string', 'default': 'default', 'label': 'Field 2'},
                'field_conflict': {'type': 'list', 'label': 'conflicting field type', 'items': {'type': 'string', 'default': 'default'}},
            }),
        )
        self.project_type_hidden = create_project_type(
            finding_fields=field_definition_to_dict(FINDING_FIELDS_CORE | {
                'field_hidden': {'type': 'string', 'default': 'default', 'label': 'Field of hidden ProjectType'},
            }),
        )
        project_hidden = create_project(project_type=self.project_type_hidden)
        self.project_type_hidden.linked_project = project_hidden
        self.project_type_hidden.save()

        self.template = create_template(data={'title': 'test', 'field1': 'f1 value', 'field2': 'f2 value'})

    def test_get_template_field_definition(self):
        assert \
            set(FindingTemplate.field_definition.keys()) == \
            set(FINDING_FIELDS_CORE.keys()) | set(FINDING_FIELDS_PREDEFINED.keys()) | {'field1', 'field2', 'field_conflict'}
        assert FindingTemplate.field_definition['field_conflict'].type == FieldDataType.STRING

    def test_delete_field_definition(self):
        old_value = self.template.main_translation.data['field1']
        del self.project_type1.finding_fields['field1']
        self.project_type1.save()
        self.template.main_translation.refresh_from_db()

        assert 'field1' not in FindingTemplate.field_definition
        assert self.template.main_translation.data_all['field1'] == old_value

    def test_change_field_type(self):
        self.project_type1.finding_fields |= {'field1': {'type': 'list', 'label': 'changed field type', 'items': {'type': 'string', 'default': 'default'}}}
        self.project_type1.save()
        self.template.refresh_from_db()

        assert FindingTemplate.field_definition['field1'].type == FieldDataType.LIST
        assert self.template.main_translation.data['field1'] == []


@pytest.mark.django_db()
class TestReportSectionDefinition:
    @pytest.fixture(autouse=True)
    def setUp(self):
        field_definition = {'type': 'string', 'default': 'default', 'label': 'Field label'}
        self.project_type = create_project_type(
            report_fields=field_definition_to_dict(REPORT_FIELDS_CORE) | {
                'field1': field_definition,
                'field2': field_definition,
                'field3': field_definition,
            },
            report_sections=[
                {'id': 'section1', 'fields': ['field1'], 'label': 'Section 1'},
                {'id': 'section2', 'fields': ['field2'], 'label': ['Section 2']},
            ],
        )
        self.project = create_project(project_type=self.project_type)

    def test_fields_in_no_section_put_it_other_section(self):
        assert set(self.project.sections.values_list('section_id', flat=True)) == {'section1', 'section2', 'other'}
        assert set(self.project.sections.get(section_id='other').section_fields) == set(REPORT_FIELDS_CORE.keys()) | {'field3'}

    def test_add_section(self):
        self.project_type.report_fields |= {'field_new': {'type': 'string', 'default': 'default', 'label': 'new field'}}
        self.project_type.report_sections += [{'id': 'section_new', 'fields': ['field_new']}]
        self.project_type.save()
        self.project.refresh_from_db()

        section_new = self.project.sections.get(section_id='section_new')
        assert section_new.section_fields == ['field_new']
        assert section_new.data['field_new'] == 'default'

    def test_delete_section(self):
        old_value = self.project.sections.get(section_id='section1').data['field1']
        report_sections = copy.deepcopy(self.project_type.report_sections)
        section1 = next(filter(lambda s: s['id'] == 'section1', report_sections))
        section2 = next(filter(lambda s: s['id'] == 'section2', report_sections))
        section2['fields'].extend(section1['fields'])
        self.project_type.report_sections = [section2]
        self.project_type.save()
        self.project.refresh_from_db()

        assert not self.project.sections.filter(section_id='section1').exists()
        assert self.project.sections.get(section_id='section2').data['field1'] == old_value

    def test_move_field_to_other_section(self):
        old_value = self.project.sections.get(section_id='section1').data['field1']
        report_sections = copy.deepcopy(self.project_type.report_sections)
        section1 = next(filter(lambda s: s['id'] == 'section1', report_sections))
        section1['fields'].remove('field1')
        section2 = next(filter(lambda s: s['id'] == 'section2', report_sections))
        section2['fields'].append('field1')
        self.project_type.report_sections = report_sections
        self.project_type.save()
        self.project.refresh_from_db()

        assert self.project.sections.filter(section_id='section1').exists()
        assert self.project.sections.get(section_id='section2').data['field1'] == old_value


@pytest.mark.django_db()
class TestTemplateTranslation:
    @pytest.fixture(autouse=True)
    def setUp(self):
        create_project_type()  # create dummy project_type to get field_defintions
        self.template = create_template(language=Language.ENGLISH_US, data={
            'title': 'Title main',
            'description': 'Description main',
            'recommendation': 'Recommendation main',
            'field_list': ['first', 'second'],
            'field_unknown': 'unknown',
        })
        self.main = self.template.main_translation
        self.trans = FindingTemplateTranslation.objects.create(template=self.template, language=Language.GERMAN_DE, title='Title translation')

    def test_template_translation_inheritance(self):
        self.trans.update_data({'title': 'Title translation', 'description': 'Description translation'})
        self.trans.save()

        data_inherited = self.trans.get_data(inherit_main=True)
        assert data_inherited['title'] == self.trans.title == 'Title translation'
        assert data_inherited['description'] == 'Description translation'
        assert data_inherited['recommendation'] == self.main.data['recommendation'] == 'Recommendation main'
        assert 'recommendation' not in self.trans.data
        assert 'field_list' not in self.trans.data

    def test_template_formatting(self):
        self.trans.custom_fields = {
            'recommendation': {'value': 'invalid format'},
            'field_list': ['first', {'value': 'invalid format'}],
            'field_object': {},
        }
        self.trans.save()
        assert 'description' not in self.trans.data
        assert self.trans.data['recommendation'] is None
        assert self.trans.data['field_list'] == ['first', None]
        assert self.trans.data['field_object']['nested1'] is None

    def test_undefined_in_main(self):
        self.main.custom_fields = {}
        self.main.save()
        data_inherited = self.trans.get_data(inherit_main=True)
        assert 'description' not in data_inherited
        assert 'field_list' not in data_inherited
        assert 'field_object' not in data_inherited

    def test_update_data(self):
        self.main.update_data({
            'title': 'new',
            'description': 'new',
        })
        self.main.save()
        data_inherited = self.trans.get_data(inherit_main=True)
        assert data_inherited['title'] != 'new'
        assert data_inherited['description'] == 'new'
        assert 'recommendation' not in data_inherited
        assert data_inherited['field_unknown'] == 'unknown'
        assert 'field_unknown' not in self.trans.data


@pytest.mark.django_db()
class TestFindingSorting:
    def assert_finding_order(self, findings_kwargs, **project_kwargs):
        findings_kwargs = reversed(self.format_findings_kwargs(findings_kwargs))
        project = create_project(
            findings_kwargs=findings_kwargs,
            **project_kwargs)
        findings_sorted = sort_findings(
            findings=[format_template_field_object(
                    {'id': str(f.id), 'created': str(f.created), 'order': f.order, **f.data},
                    definition=project.project_type.finding_fields_obj)
                for f in project.findings.all()],
            project_type=project.project_type,
            override_finding_order=project.override_finding_order,
        )
        findings_sorted_titles = [f['title'] for f in findings_sorted]
        assert findings_sorted_titles == [f'f{i + 1}' for i in range(len(findings_sorted_titles))]

    def format_findings_kwargs(self, findings_kwargs):
        for idx, finding_kwarg in enumerate(findings_kwargs):
            finding_kwarg.setdefault('data', {})
            finding_kwarg['data']['title'] = f'f{idx + 1}'
        return findings_kwargs

    def test_override_finding_order(self):
        self.assert_finding_order(override_finding_order=True, findings_kwargs=[
            {'order': 1},
            {'order': 2},
            {'order': 3},
        ])

    def test_fallback_order(self):
        self.assert_finding_order(
            override_finding_order=False,
            project_type=create_project_type(finding_ordering=[]),
            findings_kwargs=[
                {'order': 1, 'created': timezone.now() - timedelta(days=2)},
                {'order': 1, 'created': timezone.now() - timedelta(days=1)},
                {'order': 1, 'created': timezone.now() - timedelta(days=0)},
            ])

    @pytest.mark.parametrize(('finding_ordering', 'findings_kwargs'), [
        ([{'field': 'cvss', 'order': 'desc'}], [{'cvss': 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H'}, {'cvss': 'CVSS:3.1/AV:N/AC:H/PR:L/UI:R/S:C/C:L/I:L/A:L'}, {'cvss': None}]),  # CVSS
        ([{'field': 'field_string', 'order': 'asc'}], [{'field_string': 'aaa'}, {'field_string': 'bbb'}, {'field_string': 'ccc'}]),  # string field
        ([{'field': 'field_int', 'order': 'asc'}], [{'field_int': 1}, {'field_int': 10}, {'field_int': 13}]),  # number
        ([{'field': 'field_enum', 'order': 'asc'}], [{'field_enum': 'enum1'}, {'field_enum': 'enum2'}]),  # enum
        ([{'field': 'field_date', 'order': 'asc'}], [{'field_date': None}, {'field_date': '2023-01-01'}, {'field_date': '2023-06-01'}]),  # date
        ([{'field': 'field_string', 'order': 'asc'}, {'field': 'field_markdown', 'order': 'asc'}], [{'field_string': 'aaa', 'field_markdown': 'xxx'}, {'field_string': 'aaa', 'field_markdown': 'yyy'}, {'field_string': 'bbb', 'field_markdown': 'zzz'}]),  # multiple fields: string, markdown
        ([{'field': 'field_bool', 'order': 'desc'}, {'field': 'cvss', 'order': 'desc'}], [{'field_bool': True, 'cvss': 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H'}, {'field_bool': True, 'cvss': 'CVSS:3.1/AV:N/AC:H/PR:L/UI:R/S:C/C:L/I:L/A:L'}, {'field_bool': False, 'cvss': 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H'}]),  # multiple fields: -bool, -cvss
        ([{'field': 'field_enum', 'order': 'asc'}, {'field': 'field_int', 'order': 'desc'}], [{'field_enum': 'enum1', 'field_int': 2}, {'field_enum': 'enum1', 'field_int': 1}, {'field_enum': 'enum2', 'field_int': 10}, {'field_enum': 'enum2', 'field_int': 9}]),  # multiple fields with mixed asc/desc: enum, -number
    ])
    def test_finding_order_by_fields(self, finding_ordering, findings_kwargs):
        self.assert_finding_order(
            override_finding_order=False,
            project_type=create_project_type(finding_ordering=finding_ordering),
            findings_kwargs=[{'data': f} for f in findings_kwargs],
        )


@pytest.mark.django_db()
class TestDefaultNotes:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.project_type = create_project_type()

    @pytest.mark.parametrize(('valid', 'default_notes'), [
        (True, []),
        (True, [{'id': '11111111-1111-1111-1111-111111111111', 'parent': None, 'order': 1, 'checked': True, 'icon_emoji': '🦖', 'title': 'Note title', 'text': 'Note text content'}]),
        (True, [{'id': '11111111-1111-1111-1111-111111111111', 'parent': None}, {'parent': '11111111-1111-1111-1111-111111111111'}]),
        (False, [{'parent': '22222222-2222-2222-2222-222222222222'}]),
        (False, [{'id': '11111111-1111-1111-1111-111111111111', 'parent': '11111111-1111-1111-1111-111111111111'}]),
        (False, [{'id': '11111111-1111-1111-1111-111111111111', 'parent': '22222222-2222-2222-2222-222222222222'}, {'id': '22222222-2222-2222-2222-222222222222', 'parent': '11111111-1111-1111-1111-111111111111'}]),
    ])
    def test_default_notes(self, valid, default_notes):
        # Test default_notes validation
        is_valid = True
        try:
            self.project_type.default_notes = [{
                'id': str(uuid4()),
                'parent': None,
                'order': 0,
                'checked': None,
                'icon_emoji': None,
                'title': 'Note',
                'text': 'Note text',
            } | n for n in default_notes]
            self.project_type.full_clean()
            self.project_type.save()
        except ValidationError:
            is_valid = False
        assert is_valid == valid

        # Test note created from default_notes in project
        if is_valid:
            p = create_project(project_type=self.project_type)
            for dn in self.project_type.default_notes:
                n = p.notes.get(note_id=dn['id'])
                assert (str(n.parent.note_id) if n.parent else None) == dn['parent']
                assertKeysEqual(dn, n, ['order', 'checked', 'icon_emoji', 'title', 'text'])


