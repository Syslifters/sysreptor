from django.urls import path

from . import views

urlpatterns = [
    path('projects/<uuid:project_pk>/rendersections/', views.RenderSectionsView.as_view(), name='rendersections'),
    path('projects/<uuid:project_pk>/sections/', views.GetSectionsView.as_view(), name='getsections'),
]
