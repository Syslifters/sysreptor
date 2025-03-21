"""
ASGI config for sysreptor project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/stable/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.conf import settings
from django.core.asgi import get_asgi_application

from sysreptor.utils.middleware import WebsocketOriginValidatorMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sysreptor.conf.settings')
django_asgi_app = get_asgi_application()


from sysreptor.conf.urls import websocket_urlpatterns  # noqa: E402
from sysreptor.utils.elasticapm import DjangoASGITracingMiddleware  # noqa: E402

if settings.ELASTIC_APM_ENABLED:
    django_asgi_app = DjangoASGITracingMiddleware(django_asgi_app)

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': WebsocketOriginValidatorMiddleware(AuthMiddlewareStack(URLRouter(websocket_urlpatterns))),
})
