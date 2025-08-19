import logging

from rest_framework import serializers
from sysreptor.pentests.fielddefinition.sort import sort_findings
from sysreptor.pentests.models import ProjectNotebookPage
from sysreptor.pentests.rendering.entry import format_template_field_object
from sysreptor.pentests.serializers.notes import ProjectNotebookPageSerializer
from sysreptor.pentests.serializers.project import PentestFindingSerializer
from sysreptor.utils.utils import groupby_to_dict

from .importers import registry


class ScanImportSerializer(serializers.Serializer):
    importer = serializers.ChoiceField(choices=['auto'] + [i.id for i in registry.importers])
    import_as = serializers.ChoiceField(choices=['findings', 'notes'])
    file = serializers.ListField(child=serializers.FileField())

    def create(self, validated_data):
        if validated_data['importer'] == 'auto':
            def detect_importer(f):
                out = registry.auto_detect_format(f)
                if not out:
                    raise serializers.ValidationError(f"No suitable importer found for file '{f.name}'.")
                return out.id
            importer_files = groupby_to_dict(validated_data['file'], key=detect_importer)
        else:
            importer_files = {validated_data['importer']: validated_data['file']}

        try:
            if validated_data['import_as'] == 'findings':
                project = self.context['project']
                findings = []
                for importer_id, files in importer_files.items():
                    findings += registry[importer_id].parse_findings(files=files, project=project)

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
                notes = []
                for importer_id, files in importer_files.items():
                    notes += registry[importer_id].parse_notes(files=files)
                ProjectNotebookPage.objects.check_parent_and_order(notes)
                return ProjectNotebookPageSerializer(many=True, instance=notes).data
        except serializers.ValidationError:
            raise
        except Exception as ex:
            raise  # TODO: debug only
            logging.exception('Error while importing')
            raise serializers.ValidationError('Error while importing') from ex

