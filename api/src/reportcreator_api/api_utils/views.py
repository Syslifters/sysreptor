import json
import logging
import boto3
from django.http import StreamingHttpResponse
from django.conf import settings
from rest_framework import views, viewsets, routers
from rest_framework.serializers import Serializer
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.settings import api_settings
from reportcreator_api.api_utils.serializers import LanguageToolSerializer, BackupSerializer
from reportcreator_api.api_utils.healthchecks import run_healthchecks
from reportcreator_api.api_utils.permissions import IsSuperuser
from reportcreator_api.utils import backup_utils

from reportcreator_api.utils.models import Language


log = logging.getLogger(__name__)


class UtilsViewSet(viewsets.ViewSet):
    def get_serializer_class(self):
        if self.action == 'backup':
            return BackupSerializer
        elif self.action == 'spellcheck':
            return LanguageToolSerializer
        else:
            return Serializer

    def get_serializer(self, *args, **kwargs):
        return self.get_serializer_class()(*args, **kwargs)

    def list(self, *args, **kwargs):
        return routers.APIRootView(api_root_dict={
            'languages': 'utils-languages',
            'spellcheck': 'utils-spellcheck',
            'backup': 'utils-backup',
            'healthcheck': 'utils-healthcheck',
        }).get(*args, **kwargs)

    @action(detail=False)
    def languages(self, *args, **kwargs):
        langs = [{'code': l[0], 'name': l[1]} for l in Language.choices]
        return Response(langs)

    @action(detail=False, methods=['post'])
    def spellcheck(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(data=serializer.spellcheck())

    @action(detail=False, methods=['post'], permission_classes=api_settings.DEFAULT_PERMISSION_CLASSES + [IsSuperuser])
    def backup(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data

        z = backup_utils.create_backup()

        if s3_params := data.get('s3_params'):
            backup_utils.upload_to_s3_bucket(z, s3_params)
            return Response(status=200)
        else:
            response = StreamingHttpResponse(z, content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename={}'.format('files.zip')
            log.info('Sending Backup')
            return response

    @action(detail=False, methods=['get'], permission_classes=[])
    def healthcheck(self, request, *args, **kwargs):
        return run_healthchecks(settings.HEALTH_CHECKS)
