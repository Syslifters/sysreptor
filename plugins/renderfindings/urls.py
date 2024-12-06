from django.urls import path

from . import views

urlpatterns = [
    path('projects/<uuid:project_pk>/renderfindings/', views.RenderFindingsView.as_view(), name='renderfindings'),
]
