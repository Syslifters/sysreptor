from django.urls import include, path

from .views import ListAvailableImportersView, ParseImportView

urlpatterns = [
    path('projects/<uuid:project_pk>/', include([
        path('availableimporters/', ListAvailableImportersView.as_view(), name='availableimporters'),
        path('parse/', ParseImportView.as_view(), name='parse'),
    ])),
]

