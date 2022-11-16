import functools
import operator
import uuid
from django.utils.module_loading import import_string
from django.core.cache import cache
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from rest_framework.response import Response


def run_healthchecks(checks: dict[str, str]):
    res = {}
    for service, check_func_name in checks.items():
        check_func = import_string(check_func_name)
        res[service] = check_func()
    
    has_errors = not all(res.values())
    return Response(data=res, status=503 if has_errors else 200)


def check_database():
    """
    Check if the application can perform a dummy sql query
    """
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1; -- Healthcheck")
        row = cursor.fetchone()
        return row and row[0] == 1


def check_cache():
    """
    Check if the application can connect to the default cached and read/write some dummy data.
    """
    dummy = str(uuid.uuid4())
    key = "healthcheck:%s" % dummy
    cache.set(key, dummy, timeout=5)
    cached_value = cache.get(key)
    cache.delete(key)
    return cached_value == dummy


def check_migrations():
    """
    Check if django has unapplied migrations.
    """
    cache_key = __name__ + '.migration_check_cache'
    if res := cache.get(cache_key):
        return res

    executor = MigrationExecutor(connection)
    res = not executor.migration_plan(executor.loader.graph.leaf_nodes())
    if res:
        cache.set(key=cache_key, value=res, timeout=10 * 60)
    return res

