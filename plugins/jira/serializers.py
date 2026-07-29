import json

from django.core.validators import RegexValidator
from rest_framework import serializers

validate_jira_project_id_or_key = RegexValidator(
    regex=r'^[A-Za-z0-9_]+$',
    message='Invalid Jira project ID or key.',
)


def quote_jql_string(value: str) -> str:
    return json.dumps(value)


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
    jira_project = serializers.CharField(validators=[validate_jira_project_id_or_key])
    issue_type = serializers.CharField()
    issues = JiraIssueSerializer(many=True)
