

from datetime import date
from nis import cat
from uuid import UUID
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


def copy_keys(d: dict, keys: list[str]) -> dict:
    return dict(filter(lambda t: t[0] in keys, d.items()))


def omit_keys(d: dict, keys: list[str]) -> dict:
    return dict(filter(lambda t: t[0] not in keys, d.items()))


def omit_items(l: list, items: list):
    l = list(l)
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
