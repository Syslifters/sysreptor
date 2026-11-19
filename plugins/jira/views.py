import base64
import itertools

import httpx
from asgiref.sync import sync_to_async
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from sysreptor.pentests.models import PentestProject
from sysreptor.pentests.views import ProjectSubresourceMixin
from sysreptor.plugins import configuration
from sysreptor.utils.api import ViewSetAsync
from sysreptor.utils.crypto import CryptoError

from .adfmedia import (
    SYSREPTOR_IMAGE_PREFIX,
    extract_media_id,
    get_image_size,
    get_referenced_image_names,
    image_name_from_url,
    replace_image_placeholders,
    strip_image_placeholders,
)
from .serializers import (
    JiraExportSerializer,
    quote_jql_string,
    validate_jira_project_id_or_key,
)


def format_jira_errors(data: dict | None) -> str | None:
    """
    Extract messages from a Jira ErrorCollection or bulk error response.
    """
    if not isinstance(data, dict):
        return None
    msgs = []
    if data.get('errorMessages'):
        msgs = [str(m) for m in data.get('errorMessages') if m]
    elif data.get('errors'):
        errors = data.get('errors')
        if isinstance(errors, dict):
            msgs = [str(v) for v in errors.values() if v]
        elif isinstance(errors, list):
            msgs = list(dict.fromkeys(
                m for err in errors
                if (m := format_jira_errors(err.get('elementErrors')))
            ))
    return ', '.join(msgs) or None


def format_validation_error(e: ValidationError) -> str:
    detail = e.detail
    if isinstance(detail, list) and detail:
        return str(detail[0])
    return str(detail)


async def get_jira_config() -> tuple[str, dict]:
    base_url = (await configuration.aget('JIRA_URL') or '').rstrip('/')
    username = await configuration.aget('JIRA_USERNAME')
    api_token = await configuration.aget('JIRA_API_TOKEN')

    if not all([base_url, username, api_token]):
        raise ValidationError(
            'Jira plugin is not properly configured. '
            'Please configure JIRA_URL, JIRA_USERNAME, and JIRA_API_TOKEN in plugin settings.'
        )
    return base_url, {
        'Authorization': f"Basic {base64.b64encode(f"{username}:{api_token}".encode()).decode()}",
    }


async def jira_request(client: httpx.AsyncClient, method: str, endpoint: str, **kwargs) -> dict:
    base_url, auth_headers = await get_jira_config()

    try:
        response = await client.request(
            method=method, 
            url=f"{base_url}{endpoint}", 
            headers={
                **auth_headers,
                **kwargs.pop('headers', {}),
            }, 
            timeout=kwargs.pop('timeout', 10),
            **kwargs,
        )
        response.raise_for_status()
        return None if response.status_code in [204] else response.json()
    except httpx.HTTPStatusError as e:
        try:
            body = e.response.json()
        except ValueError:
            body = None
        raise ValidationError(format_jira_errors(body) or f'Jira API request failed: {e}') from e
    except httpx.HTTPError as e:
        raise ValidationError(f'Jira API request failed: {e}') from e


async def jira_get_media_id(client: httpx.AsyncClient, attachment_id: str) -> str | None:
    """
    Resolve the Media Services file ID of a Jira attachment.
    Jira has no public API for this. GET /attachment/content/{id} redirects to
    https://api.media.atlassian.com/file/<media-id>/binary?... and the ID is taken from that URL.
    """
    base_url, auth_headers = await get_jira_config()
    try:
        response = await client.get(
            f"{base_url}/rest/api/3/attachment/content/{attachment_id}",
            headers=auth_headers,
            follow_redirects=False,
            timeout=10,
        )
    except httpx.HTTPError:
        return None
    if not response.is_redirect:
        return None
    return extract_media_id(response.headers.get('location'))


def read_image_data(image) -> bytes | None:
    try:
        with image.file.open('rb') as f:
            return f.read()
    except (OSError, ValueError, CryptoError):
        return None


async def upload_attachment(client: httpx.AsyncClient, jira_key: str, name: str, data: bytes) -> str | None:
    """Upload an image as attachment. Returns the attachment ID."""
    try:
        result = await jira_request(
            client,
            method='POST',
            endpoint=f"/rest/api/3/issue/{jira_key}/attachments",
            headers={
                'X-Atlassian-Token': 'no-check',
                'Accept': 'application/json',
            },
            files={
                'file': (name, data, 'application/octet-stream'),
            },
            timeout=60,
        )
    except ValidationError:
        return None
    if isinstance(result, list) and result and result[0].get('id'):
        return str(result[0]['id'])
    return None


async def embed_images(client: httpx.AsyncClient, jira_key: str, description: dict, images_by_name: dict, existing_attachments: dict | None = None) -> dict:
    """
    Upload images referenced in the description (unless already attached to the issue)
    and replace the image placeholders with inline media nodes.
    """
    image_names = get_referenced_image_names(description)
    if not image_names:
        return description

    jira_base_url, _ = await get_jira_config()
    existing_attachments = existing_attachments or {}
    media_attrs_by_name = {}
    for name in image_names:
        image = images_by_name.get(name)
        data = read_image_data(image) if image else None
        attachment_id = existing_attachments.get(name)
        if not attachment_id and data is not None:
            attachment_id = await upload_attachment(client, jira_key, name, data)
        if not attachment_id:
            continue

        if media_id := await jira_get_media_id(client, attachment_id):
            # Same node structure the Jira editor creates for pasted images
            attrs = {'type': 'file', 'id': media_id, 'collection': ''}
        else:
            # Fallback: reference the attachment by URL (rendered with the user's Jira session)
            attrs = {'type': 'external', 'url': f"{jira_base_url}/rest/api/3/attachment/content/{attachment_id}"}
        # Without width/height the Jira renderer falls back to a small default size (250x200)
        if size := get_image_size(data):
            attrs['width'], attrs['height'] = size
        media_attrs_by_name[name] = attrs
    return replace_image_placeholders(description, media_attrs_by_name)


def get_existing_attachments(jira_issue: dict) -> dict[str, str]:
    """Map filename -> attachment ID (latest upload wins for duplicate filenames)."""
    attachments = sorted(
        jira_issue.get('fields', {}).get('attachment') or [],
        key=lambda a: int(a['id']) if str(a.get('id', '')).isdigit() else 0,
    )
    return {a['filename']: str(a['id']) for a in attachments if a.get('filename') and a.get('id')}


async def fetch_jira_projects(client: httpx.AsyncClient) -> list[dict]:
    """Fetch all Jira projects visible to the configured user, following pagination."""
    projects = []
    start_at = 0

    while True:
        data = await jira_request(
            client,
            method='GET',
            endpoint='/rest/api/3/project/search',
            params={
                'startAt': start_at,
                'maxResults': 100,
            },
        )
        values = data.get('values') or []
        projects.extend([
            {'id': p['id'], 'key': p['key'], 'name': p['name']}
            for p in values
        ])

        if data.get('isLast', True) or not values:
            break

        start_at = data.get('startAt', start_at) + len(values)

    return projects


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
        label_conditions = ' OR '.join([f'labels = {quote_jql_string(label)}' for label in issue_infos_by_label.keys()])
        search_result = await jira_request(
            client,
            method='POST',
            endpoint='/rest/api/3/search/jql',
            json={
                'jql': f'project = {quote_jql_string(jira_project)} AND ({label_conditions})',
                'fields': ['id', 'key', 'labels', 'summary', 'description', 'attachment'],
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


async def update_jira_issues(client: httpx.AsyncClient, existing_issues: list, images_by_name: dict) -> tuple[list, list, list]:
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

        # Upload new images and embed them inline (already attached images are reused)
        description = await embed_images(
            client, jira_key, existing_issue['description'], images_by_name,
            existing_attachments=get_existing_attachments(jira_issue),
        )
        
        # Check if summary or description has changed
        if (jira_fields.get('summary', '') != existing_issue['summary'] or 
            jira_fields.get('description', {}) != description):
            # Issue needs updating
            try:
                await jira_request(
                    client,
                    method='PUT',
                    endpoint=f'/rest/api/3/issue/{jira_key}',
                    json={
                        'fields': {
                            'summary': existing_issue['summary'],
                            'description': description,
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
                    'error': format_validation_error(e),
                })
        else:
            # Issue is already up to date
            unchanged_issues.append({
                'finding': existing_issue['finding'].finding_id,
                'jira_key': jira_key,
                'jira_url': f"{jira_base_url}/browse/{jira_key}",
            })
    
    return updated_issues, unchanged_issues, failed_issues


async def create_jira_issues(client: httpx.AsyncClient, issues_to_create: list, jira_project: str, issue_type: str, images_by_name: dict) -> tuple[list, list]:
    """
    Create new Jira issues in batches, upload images as attachments and embed them inline.
    
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
                                # Images can only be embedded after they are uploaded as attachments
                                'description': strip_image_placeholders(issue['description']),
                            },
                            'update': {},
                        } for issue in batch
                    ]
                }
            )
            
            # `issues` contains only successes, in request order, with failures removed.
            # Pair them by skipping failedElementNumber indexes; issues[i] is not batch[i].
            failed_indices = set()
            for error in result.get('errors') or []:
                # Error contains 'failedElementNumber' (0-indexed) and 'elementErrors'
                failed_idx = error.get('failedElementNumber', 0)
                in_batch = isinstance(failed_idx, int) and 0 <= failed_idx < len(batch)
                if in_batch:
                    failed_indices.add(failed_idx)
                failed_issues.append({
                    'finding': batch[failed_idx]['finding'].finding_id if in_batch else None,
                    'error': format_jira_errors(error.get('elementErrors')) or 'Unknown error',
                })

            successful_issues = [issue for idx, issue in enumerate(batch) if idx not in failed_indices]
            for issue_data, created in zip(successful_issues, result.get('issues') or [], strict=False):
                created_issues.append({
                    'finding': issue_data['finding'].finding_id,
                    'jira_key': created.get('key'),
                    'jira_url': f"{jira_base_url}/browse/{created.get('key')}",
                })
        except ValidationError as e:
            # Entire batch failed
            error = format_validation_error(e)
            for issue_data in batch:
                failed_issues.append({
                    'finding': issue_data['finding'].finding_id,
                    'error': error,
                })
    
    # Upload images as attachments and embed them inline in the description
    for issue_info in created_issues:
        issue = next((i for i in issues_to_create if i['finding'].finding_id == issue_info['finding']), None)
        if not issue or not get_referenced_image_names(issue['description']):
            continue
        try:
            description = await embed_images(client, issue_info['jira_key'], issue['description'], images_by_name)
            await jira_request(
                client,
                method='PUT',
                endpoint=f"/rest/api/3/issue/{issue_info['jira_key']}",
                json={'fields': {'description': description}},
            )
        except ValidationError as e:
            failed_issues.append({
                'finding': issue_info['finding'],
                'error': f"Issue {issue_info['jira_key']} created, but embedding images failed: {format_validation_error(e)}",
            })
    
    return created_issues, failed_issues


class JiraExportViewSet(ProjectSubresourceMixin, ViewSetAsync):
    serializer_class = serializers.Serializer
    queryset = PentestProject.objects.none()

    @action(detail=False, methods=['get'])
    async def projects(self, request, *args, **kwargs):
        await sync_to_async(self.get_project)()

        async with httpx.AsyncClient() as client:
            projects = await fetch_jira_projects(client)
            return Response({'projects': projects})
        
    @action(detail=False, methods=['get'])
    async def issuetypes(self, request, *args, **kwargs):
        await sync_to_async(self.get_project)()

        jira_project = request.query_params.get('jira_project')
        if not jira_project:
            raise ValidationError('jira_project query parameter is required')
        try:
            validate_jira_project_id_or_key(jira_project)
        except DjangoValidationError as e:
            raise ValidationError(e.messages) from e

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
        images_by_name = {}
        async for image in project.images.all():
            # Same normalization as the description URL, so the stored file is found under the name Jira accepts.
            if key := image_name_from_url(f'{SYSREPTOR_IMAGE_PREFIX}{image.name}'):
                images_by_name.setdefault(key, image)
        
        async with httpx.AsyncClient() as client:
            # Search for existing issues
            existing_issues, issues_to_create = await search_existing_issues(
                client, 
                validated_data['jira_project'], 
                validated_data['issues']
            )
            
            # Update existing issues (only if changed)
            updated_issues, unchanged_issues, failed_issues = await update_jira_issues(client, existing_issues, images_by_name)
            
            # Create new issues
            create_results = await create_jira_issues(
                client, 
                issues_to_create, 
                validated_data['jira_project'],
                validated_data['issue_type'],
                images_by_name,
            )
            created_issues = create_results[0]
            failed_issues.extend(create_results[1])
        
        return Response({
            'created': created_issues,
            'updated': updated_issues,
            'unchanged': unchanged_issues,
            'failed': failed_issues,
        })
