from django.urls import path

from .views import MarkdownExportView

urlpatterns = [
    path('projects/<uuid:project_pk>/markdownexport/', MarkdownExportView.as_view(), name='markdownexport'),
]
