import dataclasses
import enum
import functools
import json
from datetime import date
from inspect import isclass
from pathlib import Path
from types import GenericAlias
from typing import Any

from django.utils.deconstruct import deconstructible
from frozendict import frozendict

from sysreptor.utils.decorators import freeze_args, recursive_unfreeze
from sysreptor.utils.utils import copy_keys, is_date_string


@enum.unique
class FieldDataType(enum.Enum):
    STRING = 'string'
    MARKDOWN = 'markdown'
    CVSS = 'cvss'
    CWE = 'cwe'
    DATE = 'date'
    NUMBER = 'number'
    BOOLEAN = 'boolean'
    ENUM = 'enum'
    COMBOBOX = 'combobox'
    USER = 'user'
    JSON = 'json'
    OBJECT = 'object'
    LIST = 'list'


@enum.unique
class FieldOrigin(enum.Enum):
    CORE = 'core'
    PREDEFINED = 'predefined'
    CUSTOM = 'custom'


@enum.unique
class CvssVersion(enum.Enum):
    CVSS40 = 'CVSS:4.0'
    CVSS31 = 'CVSS:3.1'
    ANY = None


@deconstructible
@dataclasses.dataclass
class BaseField:
    id: str = ''
    type: FieldDataType = None
    label: str = ''
    help_text: str|None = None
    origin: FieldOrigin = FieldOrigin.CUSTOM
    extra_info: dict[str, Any] = dataclasses.field(default_factory=dict)


@deconstructible
@dataclasses.dataclass
class BaseStringField(BaseField):
    default: str|None = None
    required: bool = True


@deconstructible
@dataclasses.dataclass
class StringField(BaseStringField):
    spellcheck: bool = False
    pattern: str|None = None
    type: FieldDataType = FieldDataType.STRING


@deconstructible
@dataclasses.dataclass
class MarkdownField(BaseStringField):
    type: FieldDataType = FieldDataType.MARKDOWN


@deconstructible
@dataclasses.dataclass
class CvssField(BaseStringField):
    type: FieldDataType = FieldDataType.CVSS
    cvss_version: CvssVersion = CvssVersion.ANY


@deconstructible
@dataclasses.dataclass
class ComboboxField(BaseStringField):
    type: FieldDataType = FieldDataType.COMBOBOX
    suggestions: list[str] = dataclasses.field(default_factory=list)


@deconstructible
@dataclasses.dataclass
class DateField(BaseStringField):
    default: str|None = None
    required: bool = True
    type: FieldDataType = FieldDataType.DATE

    def __post_init__(self):
        if self.default and not is_date_string(self.default):
            raise ValueError('Default value is not a date', self.default)


@deconstructible
@dataclasses.dataclass
class EnumChoice:
    value: str
    label: str = None

    def __post_init__(self):
        self.label = self.value if not self.label else self.label


@deconstructible
@dataclasses.dataclass
class EnumField(BaseField):
    choices: list[EnumChoice] = dataclasses.field(default_factory=list)
    default: str|None = None
    required: bool = True
    type: FieldDataType = FieldDataType.ENUM

    def __post_init__(self):
        if self.default and self.default not in {c.value for c in self.choices}:
            raise ValueError(
                'Default value is not a valid enum choice', self.default)


@deconstructible
@dataclasses.dataclass
class CweField(BaseStringField):
    type: FieldDataType = FieldDataType.CWE

    @staticmethod
    @functools.cache
    def cwe_definitions() -> list[dict]:
        """
        CWE Terms of Use for CWE data in file cwe.json
        See https://cwe.mitre.org/about/termsofuse.html

        # Terms of Use
        CWE™ is free to use by any organization or individual for any research,
        development, and/or commercial purposes, per these CWE Terms of Use.
        Accordingly, The MITRE Corporation hereby grants you a non-exclusive,
        royalty-free license to use CWE for research, development, and commercial purposes.
        Any copy you make for such purposes is authorized on the condition that
        you reproduce MITRE's copyright designation and this license in any such copy.
        CWE is a trademark of The MITRE Corporation. Please contact cwe@mitre.org
        if you require further clarification on this issue.

        ## Disclaimers
        By accessing information through this site you (as “the user”) hereby agrees
        the site and the information is provided on an “as is” basis only without
        warranty of any kind, express or implied, including but not limited to
        implied warranties of merchantability, availability, accuracy, noninfringement,
        or fitness for a particular purpose. Use of this site and the information
        is at the user's own risk. The user shall comply with all applicable laws,
        rules, and regulations, and the data source's restrictions, when using the site.

        By contributing information to this site you (as “the contributor”) hereby
        represents and warrants the contributor has obtained all necessary permissions
        from copyright holders and other third parties to allow the contributor to contribute,
        and this site to host and display, the information and any such contribution,
        hosting, and displaying will not violate any law, rule, or regulation.
        Additionally, the contributor hereby grants all users of such information a perpetual,
        worldwide, non-exclusive, no-charge, royalty-free, irrevocable license to reproduce,
        prepare derivative works of, publicly display, publicly perform, sublicense,
        and distribute such information and all derivative works.

        The MITRE Corporation expressly disclaims any liability for any damages arising
        from the contributor's contribution of such information, the user's use of the
        site or such information, and The MITRE Corporation's hosting the tool and
        displaying the information. The foregoing disclaimer specifically includes
        but is not limited to general, consequential, indirect, incidental, exemplary,
        or special or punitive damages (including but not limited to loss of income,
        program interruption, loss of information, or other pecuniary loss)
        arising out of use of this information, no matter the cause of action,
        even if The MITRE Corporation has been advised of the possibility of such damages.
        """
        return json.loads((Path(__file__).parent / 'cwe.json').read_text())

    @staticmethod
    def is_valid_cwe(cwe):
        return cwe is None or \
            cwe in set(map(lambda c: f"CWE-{c['id']}", CweField.cwe_definitions()))

    def __post_init__(self):
        if not CweField.is_valid_cwe(self.default):
            raise ValueError('Default value is not a valid CWE')


@deconstructible
@dataclasses.dataclass
class JsonField(BaseStringField):
    type: FieldDataType = FieldDataType.JSON
    schema: dict|None = None


@deconstructible
@dataclasses.dataclass
class NumberField(BaseField):
    default: float|int|None = None
    required: bool = True
    type: FieldDataType = FieldDataType.NUMBER
    minimum: float|int|None = None
    maximum: float|int|None = None


@deconstructible
@dataclasses.dataclass
class BooleanField(BaseField):
    default: bool|None = None
    type: FieldDataType = FieldDataType.BOOLEAN


@deconstructible
@dataclasses.dataclass
class UserField(BaseField):
    required: bool = True
    type: FieldDataType = FieldDataType.USER


class FieldLookupMixin:
    fields: list[BaseField] = []

    def __post_init__(self):
        field_ids = [f.id for f in self.fields]
        duplicate_ids = set([f for f in field_ids if field_ids.count(f) > 1])
        if duplicate_ids:
            raise ValueError(f'Field IDs are not unique. Duplicate IDs: {", ".join(duplicate_ids)}')

    @property
    def field_dict(self):
        return {f.id: f for f in self.fields}

    def __contains__(self, field: str|BaseField):
        field_id = field.id if isinstance(field, BaseField) else field
        return field_id in self.field_dict

    def __getitem__(self, field_id: str) -> BaseField:
        return self.field_dict[field_id]

    def __delitem__(self, field_id: str) -> None:
        self.fields = [f for f in self.fields if f.id != field_id]

    def __or__(self, other):
        return dataclasses.replace(self, fields=list((self.field_dict | other.field_dict).values()))

    def get(self, field_id: str, default=None) -> BaseField|None:
        return self.field_dict.get(field_id, default)

    def keys(self):
        return list(self.field_dict.keys())


@deconstructible
@dataclasses.dataclass
class ObjectField(BaseField, FieldLookupMixin):
    properties: list[BaseField] = dataclasses.field(default_factory=list)
    type: FieldDataType = FieldDataType.OBJECT

    @property
    def fields(self):
        return self.properties

    @fields.setter
    def fields(self, value):
        self.properties = value


@deconstructible
@dataclasses.dataclass
class ListField(BaseField):
    items: BaseField = None
    required: bool = True
    default: list|None = None
    type: FieldDataType = FieldDataType.LIST

    def __post_init__(self):
        if not self.items:
            raise ValueError('List items definition missing')


_FIELD_DATA_TYPE_CLASSES_MAPPING = {
    FieldDataType.STRING: StringField,
    FieldDataType.MARKDOWN: MarkdownField,
    FieldDataType.CVSS: CvssField,
    FieldDataType.CWE: CweField,
    FieldDataType.DATE: DateField,
    FieldDataType.NUMBER: NumberField,
    FieldDataType.BOOLEAN: BooleanField,
    FieldDataType.ENUM: EnumField,
    FieldDataType.COMBOBOX: ComboboxField,
    FieldDataType.USER: UserField,
    FieldDataType.JSON: JsonField,
    FieldDataType.OBJECT: ObjectField,
    FieldDataType.LIST: ListField,
}


@deconstructible
@dataclasses.dataclass
class FieldDefinition(FieldLookupMixin):
    fields: list[BaseField] = dataclasses.field(default_factory=list)


def _field_from_dict(t: type, v: dict|str|Any, additional_dataclass_args=None):
    additional_dataclass_args = additional_dataclass_args or {}
    if isinstance(t, GenericAlias):
        if t.__origin__ is list and isinstance(v, list|tuple):
            return [_field_from_dict(t.__args__[0], e) for e in v]
        elif t.__origin__ is dict and isinstance(v, dict|frozendict):
            return {_field_from_dict(t.__args__[0], k): _field_from_dict(t.__args__[1], e) for k, e in v.items()}
    elif isinstance(v, t):
        return v
    elif isclass(t) and issubclass(t, enum.Enum):
        return t(v)
    elif isinstance(t, date) and isinstance(v, str):
        return date.fromisoformat(v)
    elif dataclasses.is_dataclass(t) and isinstance(v, dict|frozendict):
        field_types = {f.name: f.type for f in dataclasses.fields(t)}
        dataclass_args = {f: _field_from_dict(field_types[f], v[f]) for f in field_types if f in v} | additional_dataclass_args
        try:
            return t(**dataclass_args)
        except TypeError:
            pass
    elif (t is list or t == list|None) and isinstance(v, list|tuple):
        return recursive_unfreeze(v)

    raise ValueError('Could not decode field definition', v)


def _parse_field_definition_entry(definition: dict) -> BaseField:
    if not isinstance(definition, dict):
        raise ValueError('Field definition must be a dictionary')
    if 'type' not in definition:
        raise ValueError('Field type missing')

    type = FieldDataType(definition['type'])
    type_class = _FIELD_DATA_TYPE_CLASSES_MAPPING[type]
    additional_dataclass_args = {}
    if type == FieldDataType.OBJECT:
        additional_dataclass_args['properties'] = [_parse_field_definition_entry(definition=p) for p in definition.get('properties', [])]
    elif type == FieldDataType.LIST:
        additional_dataclass_args['items'] = _parse_field_definition_entry(definition=definition.get('items', {}))
    return _field_from_dict(type_class, definition, additional_dataclass_args=additional_dataclass_args)


@freeze_args
@functools.lru_cache
def parse_field_definition(definition: list[dict]) -> FieldDefinition:
    return FieldDefinition(fields=[_parse_field_definition_entry(d) for d in definition])


def _serialize_field_definition_entry(definition: list[BaseField]|Any, extra_info: bool|list[str] = False, only_fields: list[str]|None = None) -> Any:
    if isinstance(definition, dict|frozendict):
        return {k: _serialize_field_definition_entry(v, extra_info=extra_info, only_fields=only_fields) for k, v in definition.items()}
    elif isinstance(definition, list|tuple):
        return [_serialize_field_definition_entry(e, extra_info=extra_info, only_fields=only_fields) for e in definition]
    elif dataclasses.is_dataclass(definition):
        d = dataclasses.asdict(definition)
        if isinstance(definition, ListField):
            d['items'] = _serialize_field_definition_entry(definition.items, extra_info=extra_info, only_fields=only_fields)
        elif isinstance(definition, ObjectField):
            d['properties'] = _serialize_field_definition_entry(definition.properties, extra_info=extra_info, only_fields=only_fields)
        d_extra_info = d.pop('extra_info', {})
        if isinstance(extra_info, list|tuple):
            d |= copy_keys(d_extra_info, extra_info)
        elif extra_info:
            d |= d_extra_info
        return _serialize_field_definition_entry(d, extra_info=extra_info, only_fields=only_fields)
    elif isinstance(definition, enum.Enum):
        return definition.value
    elif isinstance(definition, date):
        return definition.isoformat()
    else:
        if only_fields:
            return copy_keys(definition, keys=only_fields)
        else:
            return definition


def serialize_field_definition(definition: FieldDefinition, **kwargs) -> list[dict]:
    return _serialize_field_definition_entry(definition.fields, **kwargs)


def parse_field_definition_legacy(field_dict: dict[str, dict], field_order: list[str]|None = None) -> FieldDefinition:
    field_order = (field_order or [])
    field_order += sorted(set(field_dict.keys()) - set(field_order))

    fields = []
    for k in field_order:
        if k not in field_dict:
            continue
        field_data = field_dict[k] | {'id': k}
        properties = field_data.pop('properties', {})
        items = field_data.pop('items', {})
        if field_data.get('type') == 'object':
            field_data['properties'] = []
        if field_data.get('type') == 'list':
            field_data['items'] = {'id': '', 'type': 'string'}
        field = _parse_field_definition_entry(field_data)
        if isinstance(field, ObjectField):
            field = dataclasses.replace(field, properties=parse_field_definition_legacy(field_dict=properties).fields)
        elif isinstance(field, ListField):
            field = dataclasses.replace(field, items=parse_field_definition_legacy(field_dict={'': items}).fields[0])
        fields.append(field)
    return FieldDefinition(fields=fields)


def serialize_field_definition_legacy(definition: FieldDefinition) -> dict:
    field_dict = {}
    for f in definition.fields:
        field_data = _serialize_field_definition_entry(f)
        field_data.pop('id')
        if isinstance(f, ObjectField):
            field_data['properties'] = serialize_field_definition_legacy(definition=FieldDefinition(fields=f.properties))
        elif isinstance(f, ListField):
            field_data['items'] = serialize_field_definition_legacy(definition=FieldDefinition(fields=[f.items]))[f.items.id]
            field_data.pop('default')
        field_dict[f.id] = field_data
    return field_dict

