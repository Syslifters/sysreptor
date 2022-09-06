
from rest_framework import views, viewsets, routers
from rest_framework.response import Response
from rest_framework.decorators import action

from reportcreator_api.utils.models import Language


class SettingsViewSet(viewsets.ViewSet):
    def list(self, *args, **kwargs):
        return routers.APIRootView(api_root_dict={
            'languages': 'settings-languages',
        }).get(*args, **kwargs)

    @action(detail=False)
    def languages(self, *args, **kwargs):
        langs = [{'code': l[0], 'name': l[1]} for l in Language.choices]
        return Response(langs)