from rest_framework import serializers


class RenderFindingsSerializer(serializers.Serializer):
    finding_ids = serializers.ListField(child=serializers.UUIDField())

    def validate_findings(self, value):
        findings_objs = list(self.context['project'].findings.all())

        for finding_id in set(value):
            finding = next((f for f in findings_objs if f.finding_id == finding_id), None)
            if not finding:
                raise serializers.ValidationError(f'Finding with id="{finding_id}" not found')
        return value


