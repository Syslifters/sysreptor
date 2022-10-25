from datetime import date
from typing import Union, Iterable, OrderedDict
import uuid


def remove_duplicates(lst: list) -> list:
    return list(dict.fromkeys(lst))


def find_all_indices(s: str, find: str):
    idx = 0
    while True:
        idx = s.find(find, idx)
        if idx == -1:
            break
        else:
            yield idx
            idx += 1


def get_key_or_attr(d: Union[dict, object], k: str, default=None):
    return d.get(k, default) if isinstance(d, (dict, OrderedDict)) else getattr(d, k, default)


def copy_keys(d: Union[dict, object], keys: Iterable[str]) -> dict:
    keys = set(keys)
    out = {}
    for k in keys:
        if isinstance(d, (dict, OrderedDict)):
            if k in d:
                out[k] = d[k]
        else:
            if hasattr(d, k):
                out[k] = getattr(d, k)
    return out


def omit_keys(d: dict, keys: Iterable[str]) -> dict:
    keys = set(keys)
    return dict(filter(lambda t: t[0] not in keys, d.items()))


def omit_items(l: Iterable, items: Iterable) -> list:
    l = list(l)
    items = set(items)
    for i in items:
        while True:
            try:
                l.remove(i)
            except ValueError:
                break
    return l


def is_uuid(val):
    try:
        uuid.UUID(val)
        return True
    except (ValueError, TypeError):
        return False


def is_date_string(val):
    try:
        date.fromisoformat(val)
        return True
    except (ValueError, TypeError):
        return False
