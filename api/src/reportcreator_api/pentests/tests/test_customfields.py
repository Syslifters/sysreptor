from uuid import uuid4
from django.core.exceptions import ValidationError
from django.test import TestCase
from reportcreator_api.pentests.customfields.types import parse_field_definition

from reportcreator_api.pentests.customfields.validators import FieldDefinitionValidator, FieldValuesValidator
from reportcreator_api.users.models import PentestUser


class FieldValidationTests(TestCase):
    def setUp(self) -> None:
        self.user = PentestUser.objects.create()

    def assertFieldDefinition(self, expected, field_definition):
        with self.subTest(field_definition):
            res_valid = True
            try:
                FieldDefinitionValidator()(field_definition)
            except ValidationError as ex:
                res_valid = False
            self.assertEqual(res_valid, expected)
    
    def assertFieldValue(self, expected, definition, value):
        with self.subTest({'definition': definition, 'value': value}):
            res_valid = True
            try:
                FieldValuesValidator(parse_field_definition(definition))(value)
            except (ValidationError, ValueError):
                res_valid = False
            self.assertEqual(res_valid, expected)


    def test_definition_formats(self):
        self.assertFieldDefinition(True, {})
        self.assertFieldDefinition(False, {'f': {}})
        self.assertFieldDefinition(False, {'f': {'type': 'string'}})
        # Test field id
        self.assertFieldDefinition(True, {'field1': {'type': 'string', 'label': 'Field 1', 'default': None}})
        self.assertFieldDefinition(True, {'fieldNumber_one': {'type': 'string', 'label': 'Field 1', 'default': None}})
        self.assertFieldDefinition(False, {'field 1': {'type': 'string', 'label': 'Field 1', 'default': None}})
        self.assertFieldDefinition(False, {'field.one': {'type': 'string', 'label': 'Field 1', 'default': None}})
        self.assertFieldDefinition(False, {'1st_field': {'type': 'string', 'label': 'Field 1', 'default': None}})
        # Test data types
        self.assertFieldDefinition(True, {
            'field_string': {'type': 'string', 'label': 'String Field', 'default': 'test'},
            'field_markdown': {'type': 'markdown', 'label': 'Markdown Field', 'default': '# test\nmarkdown'},
            'field_cvss': {'type': 'cvss', 'label': 'CVSS Field', 'default': 'n/a'},
            'field_date': {'type': 'date', 'label': 'Date Field', 'default': '2022-01-01'},
            'field_int': {'type': 'number', 'label': 'Number Field', 'default': 10},
            'field_bool': {'type': 'boolean', 'label': 'Boolean Field', 'default': False},
            'field_enum': {'type': 'enum', 'label': 'Enum Field', 'choices': [{'value': 'enum1', 'label': 'Enum Value 1'}, {'value': 'enum2', 'label': 'Enum Value 2'}], 'default': 'enum2'},
            'field_user': {'type': 'user', 'label': 'User Field'},
            'field_object': {'type': 'object', 'label': 'Nested Object', 'properties': {'nested1':  {'type': 'string', 'label': 'Nested Field'}}},
            'field_list': {'type': 'list', 'label': 'List Field', 'items': {'type': 'string'}},
            'field_list_objects': {'type': 'list', 'label': 'List of nested objects', 'items': {'type': 'object', 'properties': {'nested1': {'type': 'string', 'label': 'Nested object field', 'default': None}}}},
        })
        self.assertFieldDefinition(False, {'f': {'type': 'unknown', 'label': 'Unknown'}})
        self.assertFieldDefinition(False, {'f': {'type': 'date', 'label': 'Date', 'default': 'not a date'}})
        self.assertFieldDefinition(False, {'f': {'type': 'number', 'label': 'Number', 'default': 'not an int'}})
        self.assertFieldDefinition(False, {'f': {'type': 'enum', 'label': 'Enum Filed'}})
        self.assertFieldDefinition(False, {'f': {'type': 'enum', 'label': 'Enum Field', 'choices': []}})
        self.assertFieldDefinition(False, {'f': {'type': 'enum', 'label': 'Enum Field', 'choices': [{'value': 'v1'}]}})
        self.assertFieldDefinition(False, {'f': {'type': 'enum', 'label': 'Enum Field', 'choices': [{'value': None}]}})
        self.assertFieldDefinition(False, {'f': {'type': 'enum', 'label': 'Enum Field', 'choices': [{'label': 'Name only'}]}})
        self.assertFieldDefinition(False, {'f': {'type': 'object', 'label': 'Object Field'}})
        self.assertFieldDefinition(False, {'f': {'type': 'object', 'label': 'Object Field', 'properties': {'adsf': {}}}})
        self.assertFieldDefinition(False, {'f': {'type': 'list', 'label': 'List Field'}})
        self.assertFieldDefinition(False, {'f': {'type': 'list', 'label': 'List Field', 'items': {}}})

    def test_field_values(self):
        self.assertFieldValue(True, {
            'field_string': {'type': 'string', 'label': 'String Field', 'default': 'test'},
            'field_string2': {'type': 'string', 'label': 'String Field', 'default': None},
            'field_markdown': {'type': 'markdown', 'label': 'Markdown Field', 'default': '# test\nmarkdown'},
            'field_cvss': {'type': 'cvss', 'label': 'CVSS Field', 'default': 'n/a'},
            'field_date': {'type': 'date', 'label': 'Date Field', 'default': '2022-01-01'},
            'field_int': {'type': 'number', 'label': 'Number Field', 'default': 10},
            'field_bool': {'type': 'boolean', 'label': 'Boolean Field', 'default': False},
            'field_enum': {'type': 'enum', 'label': 'Enum Field', 'choices': [{'value': 'enum1', 'label': 'Enum Value 1'}, {'value': 'enum2', 'label': 'Enum Value 2'}], 'default': 'enum2'},
            'field_user': {'type': 'user', 'label': 'User Field'},
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
            'field_user': str(self.user.id),
            'field_object': {'nested1': 'val'},
            'field_list': ['test'],
            'field_list_objects': [{'nested1': 'test'}, {'nested1': 'values'}],
            'field_additional': 'test',
        })
        self.assertFieldValue(False, {'f': {'type': 'string'}}, {'f': {}})
        self.assertFieldValue(False, {'f': {'type': 'string'}}, {})
        self.assertFieldValue(False, {'f': {'type': 'list', 'items': {'type': 'object', 'properties': {'f': {'type': 'string'}}}}}, {'f': [{'f': 'v'}, {'f': 1}]})
        self.assertFieldValue(True, {'f': {'type': 'list', 'items': {'type': 'object', 'properties': {'f': {'type': 'string'}}}}}, {'f': [{'f': 'v'}, {'f': None}]})
        # self.assertFieldValue(False, {'f': {'type': 'user'}}, {'f': str(uuid4())})
