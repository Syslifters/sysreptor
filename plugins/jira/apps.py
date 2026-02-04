from sysreptor.plugins import (
    FieldDefinition,
    PluginConfig,
    StringField,
)


class JiraExportPluginConfig(PluginConfig):
    """
    Export findings to Atlassian Jira.
    Creates Jira issues from SysReptor findings.
    """

    plugin_id = '2cb192a0-8591-4de6-aaea-656b44370a23'
    professional_only = True

    configuration_definition = FieldDefinition(fields=[
        StringField(
            id='JIRA_URL',
            label='Jira URL',
            required=False,
            pattern='^https?://.*$',
            help_text='Base URL of your Jira instance (e.g., https://your-company.atlassian.net)'),
        StringField(
            id='JIRA_USERNAME',
            label='Jira Username',
            required=False,
            help_text='Jira username for authentication (usually your email for Cloud)'),
        StringField(
            id='JIRA_API_TOKEN',
            label='Jira API Token',
            required=False,
            help_text='API token for authentication'),
    ])


