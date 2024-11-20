from django.core.validators import URLValidator
from rest_framework import serializers

from .models import WebhookEventType


class WebhookConfigSerializer(serializers.Serializer):
    url = serializers.URLField(validators=[URLValidator(schemes=['https', 'http'])])
    headers = serializers.DictField(child=serializers.CharField(), required=False)
    events = serializers.ListField(child=serializers.ChoiceField(choices=WebhookEventType), allow_empty=False)

