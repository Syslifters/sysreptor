import contextlib
from urllib.parse import urlparse

import elasticapm
from django.apps import apps
from django.conf import settings
from django.urls import Resolver404, resolve
from elasticapm.conf import constants
from elasticapm.contrib.asgi import ASGITracingMiddleware
from elasticapm.contrib.asyncio.traces import set_context
from elasticapm.contrib.django.client import get_client
from elasticapm.utils.disttracing import TraceParent


def get_elasticapm_django_client():
    try:
        app = apps.get_app_config("elasticapm")
        return app.client
    except LookupError:
        return get_client()


class DjangoASGITracingMiddleware(ASGITracingMiddleware):
    @property
    def client(self):
        return get_elasticapm_django_client()

    @client.setter
    def client(self, _value):
        pass

    def set_transaction_name(self, method: str, url: str) -> None:
        path = urlparse(url).path
        try:
            resolver_match = resolve(path)
        except Resolver404:
            resolver_match = None

        elasticapm.set_transaction_name(f"{method} {resolver_match.route or resolver_match.url_name or path}")


def get_data_from_request(scope, event_type, event=None):
    m = DjangoASGITracingMiddleware(None)

    headers = m.get_headers(scope)
    result = {
        'method': (event.get('type') if event else None) or 'unknown',
        'socket': {'remote_address': m.get_ip(scope, headers)},
        'url': m.get_url(scope)[1],
        "cookies": headers.pop("cookies", {}),
    }
    if m.client.config.capture_headers:
        result['headers'] = headers
    if event and m.client.config.capture_body in ('all', event_type):
        result['body'] = event
    return result


def get_user_from_request(scope):
    user = scope.get('user')
    if user and not user.is_anonymous:
        return {
            'id': user.pk,
            'username': user.username,
        }
    else:
        return None


def set_transaction_name_websocket(scope, event):
    resolver_match = resolve(scope.get('path'), urlconf=settings.WEBSOCKET_URLCONF)
    route = 'unknown'
    if resolver_match:
        route = resolver_match.route or resolver_match.url_name
    event_type = event.get('type', 'unknown')

    elasticapm.set_transaction_name(f"{event_type} {route}")


@contextlib.asynccontextmanager
async def elasticapm_capture_websocket_transaction(scope, event=None):
    client = get_elasticapm_django_client()
    client.begin_transaction(
        transaction_type="websocket",
        trace_parent=TraceParent.from_headers(scope["headers"]),
    )
    try:
        set_transaction_name_websocket(scope, event)
        await set_context(get_data_from_request(scope, constants.TRANSACTION, event), key="request")
        await set_context(get_user_from_request(scope), key='user')
        yield
        elasticapm.set_transaction_outcome(constants.OUTCOME.SUCCESS, override=False)
    except Exception:
        client.capture_exception()
        elasticapm.set_transaction_outcome(constants.OUTCOME.FAILURE)
        raise
    finally:
        client.end_transaction()
