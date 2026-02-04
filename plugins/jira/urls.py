from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.trailing_slash = '/?'
router.include_format_suffixes = False

router.register('jira', views.JiraExportViewSet, basename='jira')


urlpatterns = [
    path('projects/<uuid:project_pk>/', include([
        *router.urls,
    ])),
]
