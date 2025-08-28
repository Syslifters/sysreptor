from django.urls import path

from .views import ListAvailableImportersView, ParseImportView

urlpatterns = [
    path('availableimporters/', ListAvailableImportersView.as_view(), name='availableimporters'),
    path('projects/<uuid:project_pk>/parse/', ParseImportView.as_view(), name='parse'),
]

