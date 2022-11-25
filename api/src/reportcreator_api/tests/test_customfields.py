import itertools
import pytest
from django.test import override_settings
from django.core.exceptions import ValidationError
from reportcreator_api.pentests.customfields.mixins import CustomFieldsMixin
from reportcreator_api.pentests.customfields.predefined_fields import FINDING_FIELDS_CORE, FINDING_FIELDS_PREDEFINED, REPORT_FIELDS_CORE, finding_fields_default

from reportcreator_api.pentests.customfields.types import FieldDataType, field_definition_to_dict, parse_field_definition
from reportcreator_api.pentests.customfields.validators import FieldDefinitionValidator, FieldValuesValidator
from reportcreator_api.pentests.customfields.utils import check_definitions_compatible
from reportcreator_api.pentests.models import FindingTemplate
from reportcreator_api.tests.mock import create_finding, create_project_type, create_project, create_template, create_user
from reportcreator_api.utils.utils import copy_keys



@pytest.mark.parametrize('valid,definition', [
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
    except ValidationError as ex:
        res_valid = False
    assert res_valid == valid


@pytest.mark.parametrize('valid,definition,value', [
    (True, {
            'field_string': {'type': 'string', 'label': 'String Field', 'default': 'test'},
            'field_string2': {'type': 'string', 'label': 'String Field', 'default': None},
            'field_markdown': {'type': 'markdown', 'label': 'Markdown Field', 'default': '# test\nmarkdown'},
            'field_cvss': {'type': 'cvss', 'label': 'CVSS Field', 'default': 'n/a'},
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


@pytest.mark.django_db
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


@pytest.mark.parametrize('definition,old_value,new_value', [
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


@pytest.mark.parametrize('compatible,a,b', [
    (True, {'a': {'type': 'string'}}, {'b': {'type': 'string'}}),
    (True, {'a': {'type': 'string'}}, {'a': {'type': 'string'}}),
    (True, {'a': {'type': 'string', 'label': 'left', 'default': 'left', 'required': False}}, {'a': {'type': 'string', 'label': 'right', 'defualt': 'right', 'required': True}}),
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


@pytest.mark.django_db
class TestUpdateFieldDefinition:
    @pytest.fixture(autouse=True)
    def setUp(self) -> None:
        self.project_type = create_project_type()
        self.project = create_project(project_type=self.project_type)
        self.finding = create_finding(project=self.project)

        self.project_other = create_project()
        self.finding_other = create_finding(project=self.project_other)
    
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
        self.project_type.report_fields['field_string']['default'] = default_val
        self.project_type.save()
        self.refresh_data()
        
        assert self.project.data['field_string'] != default_val

        project_new = create_project(project_type=self.project_type)
        assert project_new.data['field_string'] == default_val

    def test_change_default_finding_field(self):
        default_val = 'changed'
        self.project_type.finding_fields['field_string']['default'] = default_val
        self.project_type.save()
        self.refresh_data()

        assert self.finding.data['field_string'] != default_val

        finding_new = create_finding(project=self.project)
        assert finding_new.data['field_string'] == default_val

    def test_restore_data_report_field(self):
        old_value = self.project.data['field_string']
        old_definition = self.project_type.report_fields['field_string']

        # Delete field from definition
        del self.project_type.report_fields['field_string']
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
            'field_new': {'type': 'string', 'default': 'default', 'label': 'New field'}
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
            'field_new': {'type': 'string', 'default': 'default', 'label': 'New field'}
        })
        self.project.project_type = project_type_new
        self.project.save()
        self.refresh_data()

        assert 'field_string' not in self.finding.data
        assert self.finding.data_all['field_string'], old_value
        assert self.finding.data['field_new'], 'default'


@pytest.mark.django_db
class TestPredefinedFields:
    @pytest.fixture(autouse=True)
    def setUp(self) -> None:
        self.project_type = create_project_type(
            finding_fields=field_definition_to_dict(FINDING_FIELDS_CORE | copy_keys(FINDING_FIELDS_PREDEFINED, 'description')))
        project = create_project(project_type=self.project_type)
        self.finding = create_finding(project=project)

    def test_change_structure(self):
        with pytest.raises(ValidationError):
            self.project_type.finding_fields |= {
                'description': {'type': 'list', 'label': 'Changed', 'items': {'type': 'string', 'default': 'changed'}}
            }
            self.project_type.clean_fields()

    def test_add_conflicting_field(self):
        with pytest.raises(ValidationError):
            self.project_type.finding_fields |= {
                'recommendation': {'type': 'list', 'label': 'Changed', 'items': {'type': 'string', 'default': 'changed'}}
            }
            self.project_type.clean_fields()
    

@pytest.mark.django_db
class TestTemplateFieldDefinition:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.project_type1 = create_project_type(
            finding_fields=field_definition_to_dict(FINDING_FIELDS_CORE | {
                'field1': {'type': 'string', 'default': 'default', 'label': 'Field 1'},
                'field_conflict': {'type': 'string', 'default': 'default', 'label': 'Conflicting field type'},
            })
        )
        self.project_type2 = create_project_type(
            finding_fields=field_definition_to_dict(FINDING_FIELDS_CORE | {
                'field2': {'type': 'string', 'default': 'default', 'label': 'Field 2'},
                'field_conflict': {'type': 'list', 'label': 'conflicting field type', 'items': {'type': 'string', 'default': 'default'}}
            })
        )
        self.project_type_hidden = create_project_type(
            finding_fields=field_definition_to_dict(FINDING_FIELDS_CORE | {
                'field_hidden': {'type': 'string', 'default': 'default', 'label': 'Field of hidden ProjectType'},
            })
        )
        project_hidden = create_project(project_type=self.project_type_hidden)
        self.project_type_hidden.linked_project = project_hidden
        self.project_type_hidden.save()

        self.template = create_template(data={'title': 'test', 'field1': 'f1 value', 'field2': 'f2 value'})

        with override_settings(CACHES={'default': { 'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}):
            yield
    
    def test_get_template_field_definition(self):
        assert \
            set(FindingTemplate.field_definition.keys()) == \
            set(FINDING_FIELDS_CORE.keys()) | set(FINDING_FIELDS_PREDEFINED.keys()) | {'field1', 'field2', 'field_conflict'}
        assert FindingTemplate.field_definition['field_conflict'].type == FieldDataType.STRING

    def test_delete_field_definition(self):
        old_value = self.template.data['field1']
        del self.project_type1.finding_fields['field1']
        self.project_type1.save()
        self.template.refresh_from_db()

        assert 'field1' not in FindingTemplate.field_definition
        assert self.template.data_all['field1'] == old_value

    def test_change_field_type(self):
        self.project_type1.finding_fields |= {'field1': {'type': 'list', 'label': 'changed field type', 'items': {'type': 'string', 'default': 'default'}}}
        self.project_type1.save()
        self.template.refresh_from_db()

        assert FindingTemplate.field_definition['field1'].type == FieldDataType.LIST
        assert self.template.data['field1'] == []


@pytest.mark.django_db
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
            ]
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
        section1 = next(filter(lambda s: s['id'] == 'section1', self.project_type.report_sections))
        section2 = next(filter(lambda s: s['id'] == 'section2', self.project_type.report_sections))
        section2['fields'].extend(section1['fields'])
        self.project_type.report_sections = list(filter(lambda s: s['id'] != 'section1', self.project_type.report_sections))
        self.project_type.save()
        self.project.refresh_from_db()

        assert not self.project.sections.filter(section_id='section1').exists()
        assert self.project.sections.get(section_id='section2').data['field1'] == old_value
    
    def test_move_field_to_other_section(self):
        old_value = self.project.sections.get(section_id='section1').data['field1']
        section1 = next(filter(lambda s: s['id'] == 'section1', self.project_type.report_sections))
        section1['fields'].remove('field1')
        section2 = next(filter(lambda s: s['id'] == 'section2', self.project_type.report_sections))
        section2['fields'].append('field1')
        self.project_type.save()
        self.project.refresh_from_db()

        assert self.project.sections.filter(section_id='section1').exists()
        assert self.project.sections.get(section_id='section2').data['field1'] == old_value

