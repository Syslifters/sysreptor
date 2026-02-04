from rest_framework import serializers


class RenderSectionsSerializer(serializers.Serializer):
    sections = serializers.ListField(child=serializers.CharField())
    pdf_password = serializers.CharField(required=False, allow_blank=True)
