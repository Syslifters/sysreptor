from django.http import HttpResponse
from django.urls import path

"""
API endpoints defined by plugin.
Accessible at /api/plugins/<plugin_id>/api/...
"""
urlpatterns = [
    path('test/', lambda *args, **kwargs: HttpResponse("Hello world", content_type="text/plain")),
]
