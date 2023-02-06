import logging
from base64 import b64decode
from django.http import StreamingHttpResponse
from django.conf import settings
from django.utils import timezone
from rest_framework import viewsets, routers
from rest_framework.serializers import Serializer
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.settings import api_settings

from reportcreator_api.api_utils.serializers import LanguageToolSerializer, BackupSerializer
from reportcreator_api.api_utils.healthchecks import run_healthchecks
from reportcreator_api.api_utils.permissions import IsSystemUser
from reportcreator_api.utils import backup_utils
from reportcreator_api.utils.models import Language
from reportcreator_api.pentests.models import ProjectMemberRole


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
            'settings': 'utils-settings',
            'spellcheck': 'utils-spellcheck',
            'backup': 'utils-backup',
            'healthcheck': 'utils-healthcheck',
        }).get(*args, **kwargs)

    @action(detail=False, url_name='settings', url_path='settings', authentication_classes=[], permission_classes=[])
    def settings_endpoint(self, *args, **kwargs):
        return Response({
            'languages': [{'code': l[0], 'name': l[1]} for l in Language.choices],
            'project_member_roles': [{'role': r.role, 'default': r.default} for r in ProjectMemberRole.predefined_roles],
            'auth_providers': [{'id': k, 'name': v.get('label', k)} for k, v in settings.AUTHLIB_OAUTH_CLIENTS.items()],
        })

    @action(detail=False, methods=['post'])
    def spellcheck(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(data=serializer.spellcheck())

    @action(detail=False, methods=['post'], permission_classes=api_settings.DEFAULT_PERMISSION_CLASSES + [IsSystemUser])
    def backup(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        aes_key = data.get('aes_key')
        if aes_key:
            aes_key = b64decode(aes_key)

        z = backup_utils.create_backup()
        if aes_key:
            z = backup_utils.encrypt_backup(z, aes_key=aes_key)

        if s3_params := data.get('s3_params'):
            backup_utils.upload_to_s3_bucket(z, s3_params)
            return Response(status=200)
        else:
            response = StreamingHttpResponse(z)
            filename = f'backup-{timezone.now().isoformat()}.zip'
            if aes_key:
                filename += '.crypt'
            else:
                response['Content-Type'] = 'application/zip'
            
            response['Content-Disposition'] = f"attachment; filename={filename}"
            log.info('Sending Backup')
            return response

    @action(detail=False, methods=['get'], permission_classes=[])
    def healthcheck(self, request, *args, **kwargs):
        return run_healthchecks(settings.HEALTH_CHECKS)
