from rest_framework import viewsets

from .models import DemoPluginModel
from .serializers import DemoPluginModelSerializer


class DemoPluginModelViewSet(viewsets.ModelViewSet):
    """
    API viewset for DemoPluginModel providing CRUD operations.
    See https://www.django-rest-framework.org/api-guide/viewsets/
    """
    queryset = DemoPluginModel.objects.all()
    serializer_class = DemoPluginModelSerializer
