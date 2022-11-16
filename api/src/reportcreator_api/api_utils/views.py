import json

import boto3
import zipstream
from django.http import StreamingHttpResponse
from django.conf import settings
from rest_framework import views, viewsets, routers
from rest_framework.response import Response
from rest_framework.decorators import action
from reportcreator_api.api_utils.serializers import LanguageToolSerializer
from reportcreator_api.api_utils.healthchecks import run_healthchecks
from reportcreator_api.pentests.models import UploadedImage, UploadedAsset
from reportcreator_api.utils import logging, backup_utils

from reportcreator_api.utils.models import Language


class UtilsViewSet(viewsets.ViewSet):
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
        serializer = LanguageToolSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(data=serializer.spellcheck())

    @action(detail=False, methods=['post'])
    def backup(self, request, *args, **kwargs):
        if not settings.BACKUP_KEY or len(settings.BACKUP_KEY) < 20:
            logging.log.error('Backup key not set or too short (min 20 chars)')
            return Response(status=403)
        if request.POST.get('key') != settings.BACKUP_KEY:
            logging.log.error('Invalid backup key')
            return Response(status=403)
        if not request.user.is_authenticated or not request.user.is_superuser:
            logging.log.error('User not authenticated or not superuser')
            return Response(status=403)

        logging.log.info('Backup requested')
        z = zipstream.ZipFile(mode='w', compression=zipstream.ZIP_DEFLATED)
        z.write_iter('backup.json', backup_utils.create_dump())

        for image in UploadedImage.objects.all():
            z.write_iter("uploadedimages/" + image.file.name, image.file)

        for image in UploadedAsset.objects.all():
            z.write_iter("uploadedassets/" + image.file.name, image.file)
        if request.POST.get('s3_params'):
            s3_params = json.loads(request.POST.get('s3_params'))
            s3 = boto3.resource('s3',
                                **s3_params.get('broto3_params', {}),
                                )
            bucket = s3.Bucket(s3_params['bucket_name'])

            class Wrapper:
                def __init__(self, z):
                    self.z = z
                    self.buffer = b''
                    self.iter = z.__iter__()

                def read(self, size=8192):
                    while len(self.buffer) < size:
                        try:
                            self.buffer += next(self.iter)
                        except StopIteration:
                            break
                    ret = self.buffer[:size]

                    self.buffer = self.buffer[size:]
                    return ret

            bucket.upload_fileobj(Wrapper(z), s3_params['key'])

            return Response(status=200)

        response = StreamingHttpResponse(z, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename={}'.format('files.zip')
        logging.log.info('Sending Backup')
        return response

    @action(detail=False, methods=['get'], permission_classes=[])
    def healthcheck(self, request, *args, **kwargs):
        return run_healthchecks(settings.HEALTH_CHECKS)
