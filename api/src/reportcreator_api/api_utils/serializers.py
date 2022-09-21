import json
import requests
from urllib.parse import urljoin
from django.conf import settings
from rest_framework import serializers, exceptions

from reportcreator_api.utils.models import Language


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


class LanguageToolSerializer(serializers.Serializer):
    language = serializers.ChoiceField(choices=Language.choices)
    data = TextDataField()

    def spellcheck(self):
        if not settings.SPELLCHECK_URL:
            raise exceptions.PermissionDenied('Spell checker not configured')

        data = self.validated_data
        res = requests.post(
            url=urljoin(settings.SPELLCHECK_URL, '/v2/check'), 
            data={
                'language': data['language'],
                'data': json.dumps(data['data'], ensure_ascii=False),
            })
        return res.json()

