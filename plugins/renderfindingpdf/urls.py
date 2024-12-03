from django.urls import path

from . import views


urlpatterns = [
    path('projects/<uuid:project_pk>/renderfindingspdf/', views.RenderFindingPdfView.as_view(), name='renderfindingspdf'),
]
