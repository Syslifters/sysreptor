from datetime import date
from itertools import groupby
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
    except (ValueError, TypeError, AttributeError):
        return False


def is_date_string(val):
    try:
        date.fromisoformat(val)
        return True
    except (ValueError, TypeError, AttributeError):
        return False


def merge(*args):
    """
    Recursively merge dicts
    """
    out = None
    for d in args:
        if isinstance(d, (dict, OrderedDict)) and isinstance(out, (dict, OrderedDict)):
            for k, v in d.items():
                if k not in out:
                    out[k] = v
                else:
                    out[k] = merge(out.get(k), v)
        elif isinstance(d, list) and isinstance(out, list):
            l = []
            for i, dv in enumerate(d):
                if len(out) > i:
                    l.append(merge(out[i], dv))
                else:
                    l.append(dv)
            out = l
        else:
            out = d
    return out


def groupby_to_dict(data, key):
    return dict(map(lambda t: (t[0], list(t[1])), groupby(sorted(data, key=key), key=key)))