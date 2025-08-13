from django.urls import include, path

from .views import ListImportersView, ScanImportView

urlpatterns = [
    path('projects/<uuid:project_pk>/', include([
        path('importers/', ListImportersView.as_view(), name='listimporters'),
        path('scanimport/', ScanImportView.as_view(), name='scanimport'),
    ])),
]

