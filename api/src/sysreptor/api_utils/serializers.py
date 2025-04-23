import json
import logging
from base64 import b64decode
from functools import cached_property
from urllib.parse import urljoin

import httpx
from django.conf import settings
from rest_framework import exceptions, serializers

from sysreptor.api_utils.models import BackupLog
from sysreptor.pentests.models import Language
from sysreptor.utils.configuration import configuration

log = logging.getLogger(__name__)


class TextAnnotationField(serializers.Serializer):
    text = serializers.CharField(required=False, allow_blank=True, trim_whitespace=False)
    markup = serializers.CharField(required=False, allow_blank=True, trim_whitespace=False)
    interpretAs = serializers.CharField(required=False, allow_blank=True, trim_whitespace=False)
    offset = serializers.IntegerField(min_value=0, required=False)

    def validate(self, attrs):
        if attrs.get('text') is None and attrs.get('markup') is None:
            raise serializers.ValidationError('Either text or markup is required')
        return attrs


class TextDataField(serializers.Serializer):
    annotation = TextAnnotationField(many=True)


class LanguageToolSerializerBase(serializers.Serializer):
    async def languagetool_auth(self):
        return {
            'username': str(self.context['request'].user.id),
            'apiKey': str(self.context['request'].user.id),
        } if await configuration.aget('SPELLCHECK_DICTIONARY_PER_USER') else {
            'username': 'languagetool',
            'apiKey': 'languagetool',
        }

    async def languagetool_request(self, path, data):
        if not settings.SPELLCHECK_URL:
            raise exceptions.PermissionDenied('Spell checker not configured')

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                res = await client.post(
                    url=urljoin(settings.SPELLCHECK_URL, path),
                    data=(await self.languagetool_auth()) | data,
                )
                if res.status_code != 200:
                    raise exceptions.APIException(detail='Spellcheck error', code='spellcheck')
                return res.json()
        except httpx.ReadTimeout as ex:
            logging.warning('LanguageTool timeout. Spellcheck request took too long to complete.')
            raise exceptions.APIException(detail='Spellcheck timeout', code='spellcheck') from ex


class LanguageToolSerializer(LanguageToolSerializerBase):
    language = serializers.ChoiceField(choices=Language.choices + [('auto', 'auto')])
    data = TextDataField()

    @cached_property
    def spellcheck_languages(self):
        return [l for l in Language if l.spellcheck and (not configuration.PREFERRED_LANGUAGES or l.value in configuration.PREFERRED_LANGUAGES)]

    def validate_language(self, value):
        if value not in self.spellcheck_languages and value != 'auto':
            raise serializers.ValidationError('Spellchecking is not supported for this language')
        return value

    async def spellcheck(self):
        data = self.validated_data
        return await self.languagetool_request('/v2/check', json.loads(await configuration.aget('SPELLCHECK_LANGUAGETOOL_CONFIG') or '{}') | {
            'language': data['language'],
            'data': json.dumps(data['data'], ensure_ascii=False),
            'level': 'picky' if (await configuration.aget('SPELLCHECK_MODE_PICKY')) else 'default',
            **({
                'preferredVariants': ','.join(self.spellcheck_languages),
            } if data['language'] == 'auto' else {}),
        })


def validate_singe_word(val):
    if ' ' in val:
        raise serializers.ValidationError('Only a single word is supported')


class LanguageToolAddWordSerializer(LanguageToolSerializerBase):
    word = serializers.CharField(max_length=255, validators=[validate_singe_word])

    async def save(self):
        return await self.languagetool_request('/v2/words/add', {
            'word': self.validated_data['word'],
        })


class S3ParamsSerializer(serializers.Serializer):
    bucket_name = serializers.CharField()
    key = serializers.CharField()
    boto3_params = serializers.JSONField(required=False)


class BackupSerializer(serializers.Serializer):
    key = serializers.CharField()
    aes_key = serializers.CharField(required=False, allow_null=True)
    s3_params = S3ParamsSerializer(required=False, allow_null=True)
    check = serializers.BooleanField(default=False, required=False)

    def validate_key(self, key):
        if not settings.BACKUP_KEY or len(settings.BACKUP_KEY) < 20:
            log.error('Backup key not set or too short (min 20 chars)')
            raise serializers.ValidationError('Backup key not set or too short (min 20 chars)')
        elif key != settings.BACKUP_KEY:
            log.error('Invalid backup key')
            raise serializers.ValidationError('Invalid backup key')
        return key

    def validate_aes_key(self, value):
        if not value:
            return None

        try:
            key_bytes = b64decode(value)
            if len(key_bytes) != 32:
                raise serializers.ValidationError('Invalid key length: must be a 256-bit AES key')
            return value
        except ValueError as ex:
            raise serializers.ValidationError('Invalid base64 encoding') from ex


class BackupLogSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field='username', read_only=True)

    class Meta:
        model = BackupLog
        fields = ['id', 'created', 'type', 'user']


class CweDefinitionSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    description = serializers.CharField()
    parent = serializers.UUIDField(allow_null=True)
