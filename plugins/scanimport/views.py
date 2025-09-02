from rest_framework import views
from rest_framework.response import Response
from sysreptor.pentests.views import ProjectSubresourceMixin

from .importers import registry
from .serializers import ScanImportSerializer


class ListAvailableImportersView(views.APIView):
    def get(self, request, *args, **kwargs):
        return Response(['auto'] + [i.id for i in registry.importers])


class ParseImportView(ProjectSubresourceMixin, views.APIView):
    serializer_class = ScanImportSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'project': self.get_project()})
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        return Response(data, status=200)
    
