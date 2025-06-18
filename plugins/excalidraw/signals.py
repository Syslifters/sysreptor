from django.dispatch import receiver
from sysreptor.pentests.import_export.serializers.common import (
    ExportImportSerializer,
    MultiFormatSerializer,
)
from sysreptor.pentests.models import PentestProject
from sysreptor.plugins import signals as sysreptor_signals

from .apps import ExcalidrawPluginConfig
from .models import ProjectExcalidrawData


class ProjectExcalidrawDataExportImportSerializerV1(ExportImportSerializer):
    class Meta:
        model = ProjectExcalidrawData
        fields = ['elements']

    def create(self, validated_data):
        return super().create(validated_data | {
            'project': self.context['project'],
        })


class ExcalidrawExportImportSerializer(MultiFormatSerializer):
    serializer_formats = {
        'excalidraw/v1': ProjectExcalidrawDataExportImportSerializerV1(),
    }


@receiver(sysreptor_signals.post_export, sender=PentestProject)
def export_excalidraw_data(sender, instance, data, context, **kwargs):
    if not context.get('export_all'):
        return
    instance = ProjectExcalidrawData.objects.filter(project=instance).first()
    if not instance:
        return
    
    serializer = ExcalidrawExportImportSerializer(instance=instance, context=context)
    data.setdefault('plugins', {})[ExcalidrawPluginConfig.plugin_id] = serializer.data


@receiver(sysreptor_signals.post_import, sender=PentestProject)
def import_excalidraw_data(sender, instance, data, context, **kwargs):
    excalidraw_data = data.get('plugins', {}).get(ExcalidrawPluginConfig.plugin_id, None)
    if not excalidraw_data:
        return
    
    serializer = ExcalidrawExportImportSerializer(data=excalidraw_data, context=context | {'project': instance})
    serializer.is_valid(raise_exception=True)
    serializer.save()
