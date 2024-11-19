from django.core.validators import URLValidator
from rest_framework import serializers


class WebhookConfigSerializer(serializers.Serializer):
    url = serializers.URLField(validators=[URLValidator(schemes=['https', 'http'])])
    headers = serializers.DictField(child=serializers.CharField(), required=False)
    events = serializers.ListField(child=serializers.ChoiceField(choices=[
        'project_created', 'project_finished', 'project_archived', 'project_deleted',
        'finding_created', 'finding_deleted',
    ]), allow_empty=False)

