"""Explicit action capabilities for project-restricted API tokens.

Project/object visibility belongs in only_permitted(), not in this allowlist.
This check runs during authentication, including on views overriding permissions.
"""
import functools

from rest_framework.exceptions import PermissionDenied


@functools.cache
def project_token_actions():
    # Import lazily: authentication is imported while Django/DRF initialize views.
    from sysreptor.pentests import views

    read = {
        views.PentestProjectViewSet: {
            'GET': {'list', 'retrieve', 'tags', 'check', 'readonly', 'history_timeline'},
            'POST': {'export', 'export_bulk', 'preview', 'generate', 'md2html'},
        },
        views.PentestFindingViewSet: {'GET': {'list', 'retrieve', 'history_timeline'}},
        views.ReportSectionViewSet: {'GET': {'list', 'retrieve', 'history_timeline'}},
        views.ProjectNotebookPageViewSet: {
            'GET': {'list', 'retrieve', 'excalidraw', 'history_timeline'},
            'POST': {'export', 'export_bulk', 'export_pdf', 'export_pdf_multiple'},
        },
        views.CommentViewSet: {'GET': {'list', 'retrieve'}},
        views.CommentAnswerViewSet: {'GET': {'list', 'retrieve'}},
        views.UploadedImageViewSet: {'GET': {'list', 'retrieve', 'retrieve_by_name'}},
        views.UploadedProjectFileViewSet: {'GET': {'list', 'retrieve', 'retrieve_by_name'}},
        views.PentestProjectHistoryViewSet: {
            'GET': {'retrieve', 'finding', 'section', 'note', 'note_excalidraw', 'image_by_name', 'file_by_name'},
        },
        views.ProjectTypeViewSet: {'GET': {'retrieve'}},
        views.UploadedAssetViewSet: {'GET': {'list', 'retrieve', 'retrieve_by_name'}},
        # Explicit exception for reptor MCP's global template resource/tools.
        views.FindingTemplateViewSet: {'GET': {'list', 'retrieve'}},
    }
    write = {
        views.PentestProjectViewSet: {'POST': {'upload_image_or_file'}},
        views.PentestFindingViewSet: {
            'POST': {'create', 'sort'}, 'PUT': {'update'}, 'PATCH': {'partial_update'}, 'DELETE': {'destroy'},
        },
        views.ReportSectionViewSet: {'PUT': {'update'}, 'PATCH': {'partial_update'}},
        views.ProjectNotebookPageViewSet: {
            'POST': {'create', 'sort', 'copy', 'import_'},
            'PUT': {'update'}, 'PATCH': {'partial_update'}, 'DELETE': {'destroy'},
        },
        views.CommentViewSet: {
            'POST': {'create', 'resolve'}, 'PUT': {'update'}, 'PATCH': {'partial_update'}, 'DELETE': {'destroy'},
        },
        views.CommentAnswerViewSet: {
            'POST': {'create'}, 'PUT': {'update'}, 'PATCH': {'partial_update'}, 'DELETE': {'destroy'},
        },
        views.UploadedImageViewSet: {'POST': {'create'}, 'DELETE': {'destroy'}},
        views.UploadedProjectFileViewSet: {'POST': {'create'}, 'DELETE': {'destroy'}},
    }
    read_actions = frozenset(
        (view_class, action, method)
        for view_class, methods in read.items()
        for method, actions in methods.items()
        for action in actions
    )
    # HEAD is permitted only for the exact GET actions listed above.
    read_actions |= frozenset((view_class, action, 'HEAD') for view_class, action, method in read_actions if method == 'GET')
    write_actions = frozenset(
        (view_class, action, method)
        for view_class, methods in write.items()
        for method, actions in methods.items()
        for action in actions
    )
    return read_actions, write_actions


def check_project_token_permissions(request, token):
    view = (request.parser_context or {}).get('view')
    capability = (type(view), getattr(view, 'action', None), request.method)
    read_actions, write_actions = project_token_actions()
    if capability in read_actions or (not token.read_only and capability in write_actions):
        return
    raise PermissionDenied(
        'This operation is not permitted with this project-restricted API token.',
        code='permission_denied_with_project_token',
    )
