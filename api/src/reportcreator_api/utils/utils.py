import asyncio
import itertools
import uuid
from datetime import date, timedelta
from itertools import groupby
from typing import Any, Iterable, OrderedDict, Union

from django.utils import dateparse, timezone


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


def get_at(lst: list, idx: int, default=None):
    try:
        return lst[idx]
    except IndexError:
        return default


def get_key_or_attr(d: Union[dict, object], k: str, default=None):
    return d.get(k, default) if isinstance(d, (dict, OrderedDict)) else getattr(d, k, default)


def set_key_or_attr(d: Union[dict, object], k: str, value: Any):
    if isinstance(d, (dict, OrderedDict)):
        d[k] = value
    else:
        setattr(d, k, value)


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


def is_unique(lst):
    lst = list(lst)
    return len(lst) == len(set(lst))


def parse_date_string(val):
    out = dateparse.parse_datetime(val)
    if out is None:
        raise ValueError()
    if not timezone.is_aware(out):
        out = timezone.make_aware(out)
    return out


def merge(*args):
    """
    Recursively merge dicts
    """
    out = {}
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


def batched(iterable, n):
    "Batch data into tuples of length n. The last batch may be shorter."
    # batched('ABCDEFG', 3) --> ABC DEF G
    if n < 1:
        raise ValueError('n must be at least one')
    it = iter(iterable)
    while batch := tuple(itertools.islice(it, n)):
        yield batch


async def aretry(func, timeout=timedelta(seconds=1), interval=timedelta(seconds=0.1), retry_for=None):
    timeout_abs = timezone.now() + timeout
    while True:
        try:
            return await func()
        except Exception as ex:
            if retry_for and not isinstance(ex, retry_for):
                raise
            elif timezone.now() > timeout_abs:
                raise
            else:
                await asyncio.sleep(interval.total_seconds())
