from rest_framework import views, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from sysreptor.pentests.views import ProjectSubresourceMixin

from .serializers import ScanImportSerializer
from .importers import registry


class ListImportersView(views.APIView):
    def get(self, request, *args, **kwargs):
        return Response({
            "importers": [i.id for i in registry.importers]
        })


class ScanImportView(ProjectSubresourceMixin, views.APIView):
    serializer_class = ScanImportSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'project': self.get_project()})
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        return Response(data, status=200)
    

