from django.core.cache import cache as django_cache


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

