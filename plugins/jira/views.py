import base64
import itertools

import httpx
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from sysreptor.pentests.models import PentestProject
from sysreptor.pentests.views import ProjectSubresourceMixin
from sysreptor.plugins import configuration
from sysreptor.utils.api import ViewSetAsync

from .serializers import JiraExportIssuesSerializer


async def jira_request(client: httpx.AsyncClient, method: str, endpoint: str, **kwargs) -> dict:
    """
    Make authenticated request to Jira API.
    
    Args:
        client: httpx AsyncClient instance
        request: Django request object (to access plugin_config)
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path (without base URL)
        **kwargs: Additional arguments passed to httpx request
    
    Returns:
        JSON response data
    
    Raises:
        ValidationError: On HTTP errors or missing configuration
    """
    # Load and validate configuration
    base_url = (await configuration.aget('JIRA_URL') or '').rstrip('/')
    username = await configuration.aget('JIRA_USERNAME')
    api_token = await configuration.aget('JIRA_API_TOKEN')
    
    if not all([base_url, username, api_token]):
        raise ValidationError(
            'Jira plugin is not properly configured. '
            'Please configure JIRA_URL, JIRA_USERNAME, and JIRA_API_TOKEN in plugin settings.'
        )
    
    try:
        response = await client.request(
            method=method, 
            url=f"{base_url}{endpoint}", 
            headers={
                'Authorization': f"Basic {base64.b64encode(f"{username}:{api_token}".encode()).decode()}",
            }, 
            timeout=10,
            **kwargs,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        raise ValidationError(f'Jira API request failed: {str(e)}')


class JiraExportViewSet(ProjectSubresourceMixin, ViewSetAsync):
    serializer_class = serializers.Serializer
    queryset = PentestProject.objects.none()

    @action(detail=False, methods=['get'])
    async def projects(self, request, *args, **kwargs):
        async with httpx.AsyncClient() as client:
            data = await jira_request(client, method='GET', endpoint='/rest/api/3/project/search')
            projects = [
                {'id': p['id'], 'key': p['key'], 'name': p['name']}
                for p in data.get('values', [])
            ]
            return Response({'projects': projects})
        
    @action(detail=False, methods=['get'])
    async def issuetypes(self, request, *args, **kwargs):
        jira_project = request.query_params.get('jira_project')
        if not jira_project:
            raise ValidationError('jira_project query parameter is required')
        
        async with httpx.AsyncClient() as client:
            project = await jira_request(client, method='GET', endpoint=f'/rest/api/3/project/{jira_project}')
            issue_types = [
                {'id': it['id'], 'name': it['name']}
                for it in project.get('issueTypes', [])
                if not it.get('subtask')
            ]
            return Response({'issueTypes': issue_types})

    @action(detail=False, methods=['post'], serializer_class=JiraExportIssuesSerializer)
    async def exportissues(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        
        created_issues = []
        failed_issues = []
        jira_base_url = (await configuration.aget('JIRA_URL') or '').rstrip('/')
        async with httpx.AsyncClient() as client:
            # Process issues in batches of 50 (Jira bulk API limit)
            for batch in itertools.batched(validated_data['issues'], 50):
                batch = list(batch)
                try:
                    result = await jira_request(
                        client,
                        method='POST',
                        endpoint='/rest/api/3/issue/bulk',
                        json={
                            'issueUpdates': [
                                {
                                    'fields': {
                                        'project': {'id': validated_data['jira_project']},
                                        'issuetype': {'id': validated_data['issue_type']},
                                        'summary': issue['summary'],
                                        'description': issue['description'],
                                    },
                                    'update': {},
                                } for issue in batch
                            ]
                        }
                    )
                    
                    # Process successfully created issues
                    for idx, created in enumerate(result.get('issues', [])):
                        created_issues.append({
                            'finding_id': batch[idx].get('finding_id'),
                            'jira_key': created.get('key'),
                            'jira_url': f"{jira_base_url}/browse/{created.get('key')}",
                        })
                    
                    # Process errors
                    for error in result.get('errors', []):
                        # Error contains 'failedElementNumber' (0-indexed) and 'elementErrors'
                        failed_idx = error.get('failedElementNumber', 0)
                        error_messages = error.get('elementErrors', {}).get('errorMessages', [])
                        failed_issues.append({
                            'finding_id': batch[failed_idx].get('finding_id') if failed_idx < len(batch) else None,
                            'error': ', '.join(error_messages) if error_messages else 'Unknown error',
                        })
                except ValidationError as e:
                    # Entire batch failed
                    for issue_data in batch:
                        failed_issues.append({
                            'finding_id': issue_data.get('finding_id'),
                            'error': str(e),
                        })
        
        return Response({
            'success': created_issues,
            'failed': failed_issues,
        })
