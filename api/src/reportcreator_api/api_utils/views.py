
from rest_framework import views, viewsets, routers
from rest_framework.response import Response
from rest_framework.decorators import action
from reportcreator_api.api_utils.serializers import LanguageToolSerializer

from reportcreator_api.utils.models import Language


class UtilsViewSet(viewsets.ViewSet):
    def list(self, *args, **kwargs):
        return routers.APIRootView(api_root_dict={
            'languages': 'utils-languages',
            'spellcheck': 'utils-spellcheck',
        }).get(*args, **kwargs)

    @action(detail=False)
    def languages(self, *args, **kwargs):
        langs = [{'code': l[0], 'name': l[1]} for l in Language.choices]
        return Response(langs)

    @action(detail=False, methods=['post'])
    def spellcheck(self, request, *args, **kwargs):
        serializer = LanguageToolSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(data=serializer.spellcheck())