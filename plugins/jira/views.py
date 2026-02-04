import base64
import itertools

import httpx
from asgiref.sync import sync_to_async
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from sysreptor.pentests.models import PentestProject
from sysreptor.pentests.views import ProjectSubresourceMixin
from sysreptor.plugins import configuration
from sysreptor.utils.api import ViewSetAsync

from .serializers import JiraExportSerializer


async def jira_request(client: httpx.AsyncClient, method: str, endpoint: str, **kwargs) -> dict:
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
                **kwargs.pop('headers', {}),
            }, 
            timeout=10,
            **kwargs,
        )
        response.raise_for_status()
        return None if response.status_code in [204] else response.json()
    except httpx.HTTPError as e:
        raise ValidationError(f'Jira API request failed: {str(e)}')


async def search_existing_issues(client: httpx.AsyncClient, jira_project: str, issues: list) -> tuple[list, list]:
    """
    Search for existing Jira issues by finding labels.
    
    Returns:
        Tuple of (existing_issues, new_issues)
        - existing_issues: Dictionary mapping finding_id to issue data (key, summary, description)
        - new_issues: List of issues that don't exist in Jira yet
    """
    if not issues:
        return {}, []
    
    existing_issues = {}
    issue_infos_by_label = {f"sysreptor:finding:{issue['finding'].finding_id}": issue for issue in issues}
    
    try:
        # Search for all issues with any of these labels in the target project
        label_conditions = ' OR '.join([f'labels = "{label}"' for label in issue_infos_by_label.keys()])
        search_result = await jira_request(
            client,
            method='POST',
            endpoint='/rest/api/3/search/jql',
            json={
                'jql': f'project = {jira_project} AND ({label_conditions})',
                'fields': ['id', 'key', 'labels', 'summary', 'description'],
                'maxResults': 1000,
            }
        )
        # Map each finding ID to its corresponding Jira issue data
        for jira_issue in search_result.get('issues', []):
            issue_info = next(filter(None, (issue_infos_by_label.get(lbl) for lbl in jira_issue.get('fields', {}).get('labels', []))), None)
            if issue_info and issue_info['finding'].finding_id not in existing_issues:
                issue_info['jira_issue'] = jira_issue
                existing_issues[issue_info['finding'].finding_id] = issue_info
    except ValidationError:
        # If search fails, return empty dict (all issues will be created)
        pass
    
    new_issues = [issue for issue in issues if issue['finding'].finding_id not in existing_issues]
    existing_issues = list(existing_issues.values())
    return existing_issues, new_issues


async def update_jira_issues(client: httpx.AsyncClient, existing_issues: list) -> tuple[list, list, list]:
    """
    Update existing Jira issues that have changed.
    
    Returns:
        Tuple of (updated_issues, unchanged_issues, failed_issues)
    """
    jira_base_url = (await configuration.aget('JIRA_URL') or '').rstrip('/')

    updated_issues = []
    unchanged_issues = []
    failed_issues = []
    
    for existing_issue in existing_issues:
        jira_issue = existing_issue['jira_issue']
        jira_fields = jira_issue.get('fields', {})
        jira_key = jira_issue['key']
        
        # Check if summary or description has changed
        if (jira_fields.get('summary', '') != existing_issue['summary'] or 
            jira_fields.get('description', {}) != existing_issue['description']):
            # Issue needs updating
            try:
                await jira_request(
                    client,
                    method='PUT',
                    endpoint=f'/rest/api/3/issue/{jira_key}',
                    json={
                        'fields': {
                            'summary': existing_issue['summary'],
                            'description': existing_issue['description'],
                        }
                    }
                )
                updated_issues.append({
                    'finding': existing_issue['finding'].finding_id,
                    'jira_key': jira_key,
                    'jira_url': f"{jira_base_url}/browse/{jira_key}",
                })
            except ValidationError as e:
                failed_issues.append({
                    'finding': existing_issue['finding'].finding_id,
                    'error': f'Failed to update: {str(e)}',
                })
        else:
            # Issue is already up to date
            unchanged_issues.append({
                'finding': existing_issue['finding'].finding_id,
                'jira_key': jira_key,
                'jira_url': f"{jira_base_url}/browse/{jira_key}",
            })
    
    return updated_issues, unchanged_issues, failed_issues


async def create_jira_issues(client: httpx.AsyncClient, issues_to_create: list, jira_project: str, issue_type: str, project) -> tuple[list, list]:
    """
    Create new Jira issues in batches and upload attachments.
    
    Returns:
        Tuple of (created_issues, failed_issues)
    """
    jira_base_url = (await configuration.aget('JIRA_URL') or '').rstrip('/')

    created_issues = []
    failed_issues = []
    
    # Create new issues in batches of 50 (Jira bulk API limit)
    for batch in itertools.batched(issues_to_create, 50):
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
                                'project': {'id': jira_project},
                                'issuetype': {'id': issue_type},
                                'labels': [f'sysreptor:finding:{issue["finding"].finding_id}'],
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
                    'finding': batch[idx]['finding'].finding_id,
                    'jira_key': created.get('key'),
                    'jira_url': f"{jira_base_url}/browse/{created.get('key')}",
                })
            
            # Process errors
            for error in result.get('errors', []):
                # Error contains 'failedElementNumber' (0-indexed) and 'elementErrors'
                failed_idx = error.get('failedElementNumber', 0)
                error_messages = error.get('elementErrors', {}).get('errorMessages', [])
                failed_issues.append({
                    'finding': batch[failed_idx]['finding'].finding_id if failed_idx < len(batch) else None,
                    'error': ', '.join(error_messages) if error_messages else 'Unknown error',
                })
        except ValidationError as e:
            # Entire batch failed
            for issue_data in batch:
                failed_issues.append({
                    'finding': issue_data['finding'].finding_id,
                    'error': str(e),
                })
    
    # Upload attachments for created issues
    for issue_info in created_issues:
        finding = next((issue['finding'] for issue in issues_to_create if issue['finding'].finding_id == issue_info['finding']), None)
        if not finding:
            continue
        async for image in project.images.all():
            if not finding.is_file_referenced(image):
                continue
            try:
                await jira_request(
                    client,
                    method='POST',
                    endpoint=f"/rest/api/3/issue/{issue_info['jira_key']}/attachments",
                    headers={
                        'X-Atlassian-Token': 'no-check',
                        'Accept': 'application/json',
                    },
                    files={
                        'file': (image.name, image.file.open('rb'), 'application/octet-stream'),
                    },
                )
            except httpx.HTTPError:
                pass
    
    return created_issues, failed_issues


class JiraExportViewSet(ProjectSubresourceMixin, ViewSetAsync):
    serializer_class = serializers.Serializer
    queryset = PentestProject.objects.none()

    @action(detail=False, methods=['get'])
    async def projects(self, request, *args, **kwargs):
        await sync_to_async(self.get_project)()

        async with httpx.AsyncClient() as client:
            data = await jira_request(client, method='GET', endpoint='/rest/api/3/project/search')
            projects = [
                {'id': p['id'], 'key': p['key'], 'name': p['name']}
                for p in data.get('values', [])
            ]
            return Response({'projects': projects})
        
    @action(detail=False, methods=['get'])
    async def issuetypes(self, request, *args, **kwargs):
        await sync_to_async(self.get_project)()

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

    @action(detail=False, methods=['post'], serializer_class=JiraExportSerializer)
    async def export(self, request, *args, **kwargs):
        serializer = await self.aget_valid_serializer(data=request.data)
        validated_data = serializer.validated_data
        project = serializer.context['project']
        
        async with httpx.AsyncClient() as client:
            # Search for existing issues
            existing_issues, issues_to_create = await search_existing_issues(
                client, 
                validated_data['jira_project'], 
                validated_data['issues']
            )
            
            # Update existing issues (only if changed)
            updated_issues, unchanged_issues, failed_issues = await update_jira_issues(client, existing_issues)
            
            # Create new issues
            create_results = await create_jira_issues(
                client, 
                issues_to_create, 
                validated_data['jira_project'],
                validated_data['issue_type'],
                project
            )
            created_issues = create_results[0]
            failed_issues.extend(create_results[1])
        
        return Response({
            'created': created_issues,
            'updated': updated_issues,
            'unchanged': unchanged_issues,
            'failed': failed_issues,
        })
