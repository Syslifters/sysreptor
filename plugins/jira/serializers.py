from rest_framework import serializers


class JiraIssueSerializer(serializers.Serializer):
    finding_id = serializers.UUIDField()
    summary = serializers.CharField()
    description = serializers.DictField()


class JiraExportIssuesSerializer(serializers.Serializer):
    jira_project = serializers.CharField()
    issue_type = serializers.CharField()
    issues = JiraIssueSerializer(many=True)
