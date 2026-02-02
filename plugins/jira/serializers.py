from rest_framework import serializers


class JiraIssueSerializer(serializers.Serializer):
    finding = serializers.UUIDField()
    summary = serializers.CharField()
    description = serializers.DictField()

    def validate_finding(self, value):
        finding = next((f for f in self.context['project'].findings.all() if f.finding_id == value), None)
        if not finding:
            raise serializers.ValidationError(f'Finding with ID {value} does not exist in the project.')
        return finding


class JiraExportSerializer(serializers.Serializer):
    jira_project = serializers.CharField()
    issue_type = serializers.CharField()
    issues = JiraIssueSerializer(many=True)
