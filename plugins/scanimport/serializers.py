import logging

from rest_framework import serializers
from sysreptor.pentests.fielddefinition.sort import sort_findings
from sysreptor.pentests.models import ProjectNotebookPage
from sysreptor.pentests.rendering.entry import format_template_field_object
from sysreptor.pentests.serializers.notes import ProjectNotebookPageSerializer
from sysreptor.pentests.serializers.project import PentestFindingSerializer

from .importers import registry


class ScanImportSerializer(serializers.Serializer):
    importer = serializers.ChoiceField(choices=['auto'] + [i.id for i in registry.importers])
    import_as = serializers.ChoiceField(choices=['findings', 'notes'])
    file = serializers.FileField()

    def validate_importer(self, value):
        if value == 'auto':
            out = registry.auto_detect_format(self.initial_data['file'])
            if not out:
                raise serializers.ValidationError("No suitable importer found for the provided file.")
            return out
        else:
            return registry[value]

    def create(self, validated_data):
        importer = validated_data['importer']

        try:
            if validated_data['import_as'] == 'findings':
                project = self.context['project']
                findings = importer.parse_findings(file=validated_data['file'], project=project)

                # Sort findings
                findings_sorted_data = sort_findings([
                    format_template_field_object(
                        {'id': str(f.id), 'created': str(f.created), 'order': f.order, **f.data},
                        definition=project.project_type.finding_fields_obj)
                    for f in findings], project_type=project.project_type)
                findings_sorted_ids = [f['id'] for f in findings_sorted_data]
                findings_sorted = sorted(findings, key=lambda f: findings_sorted_ids.index(str(f.id)))

                return PentestFindingSerializer(many=True, instance=findings_sorted).data
            elif validated_data['import_as'] == 'notes':
                notes = importer.parse_notes(validated_data['file'])
                ProjectNotebookPage.objects.check_parent_and_order(notes)
                return ProjectNotebookPageSerializer(many=True, instance=notes).data
        except Exception as ex:
            raise  # TODO: debug only
            logging.exception(f'Error while importing importer={importer.id}')
            raise serializers.ValidationError('Error while importing') from ex

