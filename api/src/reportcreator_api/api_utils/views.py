import logging
from asgiref.sync import sync_to_async
from base64 import b64decode
from django.conf import settings
from django.utils import timezone
from rest_framework import viewsets, routers
from rest_framework.serializers import Serializer
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.settings import api_settings

from reportcreator_api.api_utils.serializers import LanguageToolAddWordSerializer, LanguageToolSerializer, BackupSerializer
from reportcreator_api.api_utils.healthchecks import run_healthchecks
from reportcreator_api.api_utils.permissions import IsSystemUser, IsUserManagerOrSuperuserOrSystem
from reportcreator_api.api_utils import backup_utils
from reportcreator_api.users.models import AuthIdentity, PentestUser
from reportcreator_api.utils.api import GenericAPIViewAsync, StreamingHttpResponseAsync
from reportcreator_api.utils import license
from reportcreator_api.pentests.models import Language
from reportcreator_api.pentests.models import ProjectMemberRole
from reportcreator_api.tasks.models import PeriodicTask
from reportcreator_api.utils.utils import copy_keys, remove_duplicates


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
            'license': 'utils-license',
            'spellcheck': 'utils-spellcheck',
            'backup': 'utils-backup',
            'healthcheck': 'utils-healthcheck',
        }).get(*args, **kwargs)

    @action(detail=False, url_name='settings', url_path='settings', authentication_classes=[], permission_classes=[])
    def settings_endpoint(self, *args, **kwargs):
        languages = [{
            'code': l.value, 
            'name': l.label, 
            'spellcheck': l.spellcheck, 
            'enabled': not settings.PREFERRED_LANGUAGES or l.value in settings.PREFERRED_LANGUAGES
        } for l in remove_duplicates(list(map(Language, settings.PREFERRED_LANGUAGES)) + list(Language))]

        auth_providers = \
            ([{'type': 'local', 'id': 'local', 'name': 'Local User'}] if settings.LOCAL_USER_AUTH_ENABLED or not license.is_professional() else []) + \
            ([{'type': AuthIdentity.PROVIDER_REMOTE_USER, 'id': AuthIdentity.PROVIDER_REMOTE_USER, 'name': 'Remote User'}] if settings.REMOTE_USER_AUTH_ENABLED and license.is_professional() else []) + \
            ([{'type': 'oidc', 'id': k, 'name': v.get('label', k)} for k, v in settings.AUTHLIB_OAUTH_CLIENTS.items()] if license.is_professional() else [])

        return Response({
            'languages': languages,
            'project_member_roles': [{'role': r.role, 'default': r.default} for r in ProjectMemberRole.predefined_roles],
            'auth_providers': auth_providers,
            'default_auth_provider': settings.DEFAULT_AUTH_PROVIDER,
            'default_reauth_provider': settings.DEFAULT_REAUTH_PROVIDER,
            'elastic_apm_rum_config': settings.ELASTIC_APM_RUM_CONFIG if settings.ELASTIC_APM_RUM_ENABLED else None,
            'archiving_threshold': settings.ARCHIVING_THRESHOLD,
            'license': copy_keys(license.check_license(), ['type', 'error']),
            'features': {
                'private_designs': settings.ENABLE_PRIVATE_DESIGNS,
                'spellcheck': bool(settings.SPELLCHECK_URL and license.is_professional()),
                'archiving': license.is_professional(),
            },
        })

    @action(detail=False, methods=['post'], permission_classes=api_settings.DEFAULT_PERMISSION_CLASSES + [IsSystemUser, license.ProfessionalLicenseRequired])
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
            response = StreamingHttpResponseAsync(backup_utils.to_chunks(z))
            filename = f'backup-{timezone.now().isoformat()}.zip'
            if aes_key:
                filename += '.crypt'
            else:
                response['Content-Type'] = 'application/zip'
            
            response['Content-Disposition'] = f"attachment; filename={filename}"
            log.info('Sending Backup')
            return response
        
    @action(detail=False, methods=['get'], permission_classes=api_settings.DEFAULT_PERMISSION_CLASSES + [IsUserManagerOrSuperuserOrSystem])
    def license(self, request, *args, **kwargs):
        return Response(data=license.check_license() | {
            'active_users': PentestUser.objects.get_licensed_user_count(),
            'software_version': settings.VERSION,
        })


class SpellcheckView(GenericAPIViewAsync):
    serializer_class = LanguageToolSerializer
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES + [license.ProfessionalLicenseRequired]

    async def post(self, request, *args, **kwargs):
        serializer = await self.aget_valid_serializer(data=request.data)
        data = await serializer.spellcheck()
        return Response(data=data)
    

class SpellcheckWordView(GenericAPIViewAsync):
    serializer_class = LanguageToolAddWordSerializer
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES + [license.ProfessionalLicenseRequired]

    async def post(self, request, *args, **kwargs):
        serializer = await self.aget_valid_serializer(data=request.data)
        data = await serializer.save()
        return Response(data=data)


class HealthcheckView(GenericAPIViewAsync):
    authentication_classes = []
    permission_classes = []

    async def get(self, *args, **kwargs):
        # Trigger periodic tasks
        await PeriodicTask.objects.run_all_pending_tasks()

        return await sync_to_async(run_healthchecks)(settings.HEALTH_CHECKS)

