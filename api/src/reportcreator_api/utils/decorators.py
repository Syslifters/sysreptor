import functools

from django.core.cache import cache as django_cache
from frozendict import frozendict


def cache(key, **cache_kwargs):
    def inner(func):
        def wrapped(*args, **kwargs):
            val = django_cache.get(key)
            if val is not None:
                return val
            else:
                val = func(*args, **kwargs)
                django_cache.set(key=key, value=val, **cache_kwargs)
                return val
        return wrapped
    return inner


def acache(key, **cache_kwargs):
    def inner(func):
        async def wrapped(*args, **kwargs):
            val = await django_cache.aget(key)
            if val is not None:
                return val
            else:
                val = await func(*args, **kwargs)
                await django_cache.aset(key=key, value=val, **cache_kwargs)
                return val
        return wrapped
    return inner


def recursive_freeze(value):
    if isinstance(value, dict):
        return frozendict({k: recursive_freeze(v) for k, v in value.items()})
    elif isinstance(value, list):
        return tuple([recursive_freeze(v) for v in value])
    else:
        return value


def freeze_args(func):
    """
    Transform mutable dictionnary into immutable.
    Useful to be compatible with cache
    """

    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        args = tuple([recursive_freeze(arg) if isinstance(arg, (dict, list)) else arg for arg in args])
        kwargs = {k: recursive_freeze(v) if isinstance(v, (dict, list)) else v for k, v in kwargs.items()}
        return func(*args, **kwargs)
    return wrapped
