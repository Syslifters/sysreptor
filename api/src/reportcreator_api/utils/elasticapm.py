from urllib.parse import urlparse

import elasticapm
from django.apps import apps
from django.urls import Resolver404, resolve
from elasticapm.contrib.asgi import ASGITracingMiddleware


class DjangoASGITracingMiddleware(ASGITracingMiddleware):
    @property
    def client(self):
        app = apps.get_app_config("elasticapm")
        return app.client

    @client.setter
    def client(self, _value):
        pass

    def set_transaction_name(self, method: str, url: str) -> None:
        path = urlparse(url).path
        try:
            resolver_match = resolve(path)
        except Resolver404:
            resolver_match = None

        if resolver_match:
            elasticapm.set_transaction_name(resolver_match.route or resolver_match.url_name)
        else:
            return super().set_transaction_name(method, url)
