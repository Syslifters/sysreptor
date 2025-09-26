import dataclasses
import enum
import random
from collections.abc import Iterable
from typing import Any

from django.utils import timezone
from lorem_text import lorem

from sysreptor.utils.fielddefinition.types import (
    BaseField,
    CweField,
    FieldDataType,
    FieldDefinition,
    FieldOrigin,
    ObjectField,
)
from sysreptor.utils.utils import is_date_string, is_uuid


def contains(a: dict, b: dict) -> bool:
    """
    Checks if dict a contains dict b recursively
    """
    if not b:
        return True

    if type(a) is not type(b):
        return False

    for k, v in b.items():
        if k not in a:
            return False
        if isinstance(v, dict):
            if not contains(a[k], v):
                return False
        elif isinstance(v, list|tuple):
            raise ValueError('Cannot diff lists')
        elif v != b[k]:
            return False
    return True


def has_field_structure_changed(old: FieldDefinition|ObjectField, new: FieldDefinition|ObjectField) -> bool:
    if type(old) is not type(new):
        return True

    old_fields = old.field_dict
    new_fields = new.field_dict
    if set(old_fields.keys()) != set(new_fields.keys()):
        return True

    for k in old_fields.keys():
        field_type = old_fields[k].type
        if field_type != new_fields[k].type:
            return True
        elif field_type == FieldDataType.OBJECT and has_field_structure_changed(old_fields[k], new_fields[k]):
            return True
        elif field_type == FieldDataType.LIST and has_field_structure_changed(FieldDefinition(fields=[old_fields[k].items]), FieldDefinition(fields=[new_fields[k].items])):
            return True
        elif field_type == FieldDataType.ENUM and set(map(lambda c: c.value, old[k].choices)) - set(map(lambda c: c.value, new[k].choices)):
            # Existing enum choice was removed
            return True

    return False


class HandleUndefinedFieldsOptions(enum.Enum):
    FILL_NONE = 'fill_none'
    FILL_DEFAULT = 'fill_default'
    FILL_DEMO_DATA = 'fill_demo_data'


def _default_or_demo_data(definition: BaseField, demo_data: Any, handle_undefined: HandleUndefinedFieldsOptions):
    if handle_undefined == HandleUndefinedFieldsOptions.FILL_NONE:
        return None
    elif handle_undefined == HandleUndefinedFieldsOptions.FILL_DEFAULT:
        return getattr(definition, 'default', None)
    elif handle_undefined == HandleUndefinedFieldsOptions.FILL_DEMO_DATA:
        return getattr(definition, 'default', None) or demo_data


def ensure_defined_structure(value, definition: FieldDefinition|BaseField, handle_undefined: HandleUndefinedFieldsOptions = HandleUndefinedFieldsOptions.FILL_DEFAULT, include_unknown=False):
    """
    Ensure that the returned data is valid for the given field definition.
    Recursively check for undefined fields and set a value.
    Returns only data of defined fields, if value contains undefined fields, this data is not returned.
    """
    if isinstance(definition, FieldDefinition|ObjectField):
        out = value.copy() if include_unknown else {}
        for f in definition.fields:
            out[f.id] = ensure_defined_structure(value=(value if isinstance(value, dict) else {}).get(f.id), definition=f, handle_undefined=handle_undefined)
        return out
    elif definition.type == FieldDataType.LIST:
        if isinstance(value, list):
            return [ensure_defined_structure(value=e, definition=definition.items, handle_undefined=handle_undefined) for e in value]
        elif value:
            # Wrap single value in list
            return [ensure_defined_structure(value=value, definition=definition.items, handle_undefined=handle_undefined)]
        else:
            if handle_undefined == HandleUndefinedFieldsOptions.FILL_DEMO_DATA and definition.items.type != FieldDataType.USER:
                return [ensure_defined_structure(value=None, definition=definition.items, handle_undefined=handle_undefined) for _ in range(2)]
            elif handle_undefined == HandleUndefinedFieldsOptions.FILL_DEFAULT and isinstance(definition.default, list):
                return [ensure_defined_structure(value=e, definition=definition.items, handle_undefined=handle_undefined) for e in definition.default]
            else:
                return []
    elif definition.type != FieldDataType.LIST and isinstance(value, list) and len(value) > 0:
        return ensure_defined_structure(value=value[0], definition=definition, handle_undefined=handle_undefined)
    elif definition.type == FieldDataType.MARKDOWN and not isinstance(value, str):
        return _default_or_demo_data(definition, lorem.paragraphs(3), handle_undefined=handle_undefined)
    elif definition.type == FieldDataType.STRING and not isinstance(value, str):
        return _default_or_demo_data(definition, lorem.words(2), handle_undefined=handle_undefined)
    elif definition.type == FieldDataType.CVSS and not isinstance(value, str):
        return _default_or_demo_data(definition, 'n/a', handle_undefined=handle_undefined)
    elif definition.type == FieldDataType.ENUM and not (isinstance(value, str) and value in {c.value for c in definition.choices}):
        return _default_or_demo_data(definition, next(iter(map(lambda c: c.value, definition.choices)), None), handle_undefined=handle_undefined)
    elif definition.type == FieldDataType.CWE and not (isinstance(value, str) and CweField.is_valid_cwe(value)):
        return _default_or_demo_data(definition, 'CWE-89', handle_undefined=handle_undefined)
    elif definition.type == FieldDataType.COMBOBOX and not isinstance(value, str):
        return _default_or_demo_data(definition, next(iter(definition.suggestions), None), handle_undefined=handle_undefined)
    elif definition.type == FieldDataType.DATE and not (isinstance(value, str) and is_date_string(value)):
        return _default_or_demo_data(definition, timezone.now().date().isoformat(), handle_undefined=handle_undefined)
    elif definition.type == FieldDataType.NUMBER and not isinstance(value, int|float):
        return _default_or_demo_data(definition, random.randint(1, 10), handle_undefined=handle_undefined)  # noqa: S311
    elif definition.type == FieldDataType.BOOLEAN and not isinstance(value, bool):
        return _default_or_demo_data(definition, random.choice([True, False]), handle_undefined=handle_undefined)  # noqa: S311
    elif definition.type == FieldDataType.JSON and not isinstance(value, str):
        return _default_or_demo_data(definition, None, handle_undefined=handle_undefined)
    elif definition.type == FieldDataType.USER and not is_uuid(value):
        return None
    else:
        return value


def check_definitions_compatible(a: FieldDefinition|BaseField, b: FieldDefinition|BaseField, path: tuple[str] | None = None) -> tuple[bool, list[str]]:
    """
    Check if definitions are compatible and values can be converted without data loss.
    """
    from sysreptor.pentests.rendering.error_messages import format_path

    path = path or tuple()
    valid = True
    errors = []
    if isinstance(a, FieldDefinition|ObjectField) and isinstance(b, FieldDefinition|ObjectField):
        a_fields = a.field_dict
        b_fields = b.field_dict
        for k in set(a_fields.keys()).intersection(b_fields.keys()):
            res_valid, res_errors = check_definitions_compatible(a=a_fields[k], b=b_fields[k], path=path + tuple([k]))
            valid = valid and res_valid
            errors.extend(res_errors)
    elif isinstance(a, BaseField) and isinstance(b, BaseField):
        if a.type != b.type:
            valid = False
            errors.append(f'Field "{format_path(path)}" has different types: "{a.type.value}" vs. "{b.type.value}"')
        elif a.type == FieldDataType.LIST:
            res_valid, res_errors = check_definitions_compatible(a.items, b.items, path=path + tuple(['[]']))
            valid = valid and res_valid
            errors.extend(res_errors)
        elif a.type == FieldDataType.ENUM:
            missing_choices = {c.value for c in a.choices} - {c.value for c in b.choices}
            if missing_choices:
                valid = False
                missing_choices_str = ', '.join(map(lambda c: f'"{c}"', missing_choices))
                errors.append(f'Field "{format_path(path)}" has missing enum choices: {missing_choices_str}')
    return valid, errors


def set_field_origin(definition: FieldDefinition|BaseField, predefined_fields: FieldDefinition|BaseField|None):
    """
    Sets definition.origin recursively
    """
    if isinstance(definition, FieldDefinition):
        return FieldDefinition(fields=[
            set_field_origin(f, predefined_fields=predefined_fields.get(f.id) if isinstance(predefined_fields, FieldDefinition) else None)
            for f in definition.fields
        ])
    else:
        out = dataclasses.replace(definition, origin=getattr(predefined_fields, 'origin', FieldOrigin.CUSTOM))

        if out.type == FieldDataType.OBJECT:
            out.properties = [
                set_field_origin(f, predefined_fields=predefined_fields.get(f.id) if isinstance(predefined_fields, ObjectField) else None)
                for f in definition.properties
            ]
        elif out.type == FieldDataType.LIST:
            out.items = set_field_origin(out.items, predefined_fields=getattr(predefined_fields, 'items', None))
        return out


def iterate_fields(value: dict | Any, definition: FieldDefinition|BaseField, path: tuple[str] | None = None) -> Iterable[tuple[tuple[str], Any, BaseField]]:
    """
    Recursively iterate over all defined fields
    """
    if not definition:
        return

    path = path or tuple()
    # Current field
    if isinstance(definition, BaseField):
        yield path, value, definition

    # Nested structures
    if isinstance(definition, FieldDefinition|ObjectField):
        for f in definition.fields:
            yield from iterate_fields(value=(value if isinstance(value, dict) else {}).get(f.id), definition=f, path=path + tuple([f.id]))
    elif definition.type == FieldDataType.LIST:
        for idx, v in enumerate(value if isinstance(value, list) else []):
            yield from iterate_fields(value=v, definition=definition.items, path=path + tuple(['[' + str(idx) + ']']))


def get_field_value_and_definition(data: dict, definition: FieldDefinition, path: str|tuple|list[str]) -> tuple[tuple, Any, BaseField]:
    """
    Get value and definition at path in dict
    """
    if isinstance(path, str):
        path = tuple(path.split('.'))
    elif isinstance(path, list):
        path = tuple(path)

    for p, v, d in iterate_fields(value=data, definition=definition):
        if p == path:
            return p, v, d
    raise KeyError('.'.join(path))


def get_value_at_path(obj: dict, path: tuple[str]):
    """
    Get value at path in dict
    """
    value = obj
    for p in path:
        if isinstance(value, list|tuple) and p.startswith('[') and p.endswith(']') and p[1:-1].isdigit():
            idx = int(p[1:-1])
            if not (0 <= idx < len(value)):
                return None
            value = value[idx]
        elif isinstance(value, dict) and p in value:
            value = value[p]
        else:
            return None
    return value


def set_value_at_path(obj: dict, path: tuple[str], value: Any):
    for idx, p in enumerate(path):
        is_last = idx == len(path) - 1
        if isinstance(obj, list) and p.startswith('[') and p.endswith(']') and p[1:-1].isdigit():
            idx = int(p[1:-1])
            if not (0 <= idx < len(obj)):
                return False
            if is_last:
                obj[idx] = value
                return True
            else:
                obj = obj[idx]
        elif isinstance(obj, dict) and p in obj:
            if is_last:
                obj[p] = value
                return True
            else:
                obj = obj[p]
        else:
            return False
    return False
