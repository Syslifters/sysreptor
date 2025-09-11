from django.dispatch import receiver
from rest_framework import serializers
from sysreptor.pentests.import_export.serializers.common import (
    MultiFormatSerializer,
)
from sysreptor.pentests.models import NoteType, PentestProject, ProjectNotebookPage
from sysreptor.plugins import signals as sysreptor_signals

from .apps import ExcalidrawPluginConfig


class ProjectExcalidrawDataExportImportSerializerV1(serializers.Serializer):
    elements = serializers.JSONField()

    class Meta:
        fields = ['elements']

    def create(self, validated_data):
        if elements := validated_data.get('elements', []):
            instance = ProjectNotebookPage.objects.create(
                project=self.context['project'],
                type=NoteType.EXCALIDRAW,
                title='Excalidraw',
            )
            instance.update_excalidraw_data({'elements': elements})
            return instance


class ExcalidrawExportImportSerializer(MultiFormatSerializer):
    serializer_formats = {
        'excalidraw/v1': ProjectExcalidrawDataExportImportSerializerV1(),
    }


@receiver(sysreptor_signals.post_import, sender=PentestProject)
def import_excalidraw_data(sender, instance, data, context, **kwargs):
    excalidraw_data = data.get('plugins', {}).get(ExcalidrawPluginConfig.plugin_id, None)
    if not excalidraw_data:
        return
    
    serializer = ExcalidrawExportImportSerializer(data=excalidraw_data, context=context | {'project': instance})
    serializer.is_valid(raise_exception=True)
    serializer.save()
