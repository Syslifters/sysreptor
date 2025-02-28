from django.http import HttpResponse
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .consumers import DemoPluginConsumer
from .views import DemoPluginModelViewSet

router = DefaultRouter()
router.register('demopluginmodels', DemoPluginModelViewSet, basename='demopluginmodel')


"""
API endpoints defined by plugin.
Accessible at /api/plugins/<plugin_id>/api/...
"""
urlpatterns = [
    path('helloworld/', lambda *args, **kwargs: HttpResponse("Hello world", content_type="text/plain"), name='helloworld'),
    path('', include(router.urls)),
]


"""
WebSocket consumers defined by plugin.
Accessible at /api/plugins/<plugin_id>/ws/...
"""
websocket_urlpatterns = [
    path('projects/<uuid:project_pk>/hellowebsocket/', DemoPluginConsumer.as_asgi(), name='hellowebsocket'),
]


