from django.urls import path

from .consumers import ExcalidrawConsumer

websocket_urlpatterns = [
    path('projects/<uuid:project_pk>/excalidraw/', ExcalidrawConsumer.as_asgi(), name='excalidraw'),
]
