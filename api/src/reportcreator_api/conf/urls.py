from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from django.http import HttpResponse
from django.views.generic.base import TemplateView, RedirectView
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter

from reportcreator_api.api_utils.views import SpellcheckWordView, UtilsViewSet, SpellcheckView, HealthcheckView
from reportcreator_api.pentests.views import ArchivedProjectKeyPartViewSet, ArchivedProjectViewSet, FindingTemplateViewSet, PentestFindingViewSet, PentestProjectViewSet, ProjectNotebookPageViewSet, \
    PentestProjectPreviewView, PentestProjectGenerateView, \
    ProjectTypeViewSet, ProjectTypePreviewView, \
    ReportSectionViewSet, UploadedAssetViewSet, UploadedImageViewSet, UploadedProjectFileViewSet, UploadedUserNotebookImageViewSet, UserNotebookPageViewSet, UserPublicKeyViewSet
from reportcreator_api.users.views import PentestUserViewSet, MFAMethodViewSet, AuthViewSet, AuthIdentityViewSet
from reportcreator_api.notifications.views import NotificationViewSet


router = DefaultRouter()
router.register('pentestusers', PentestUserViewSet, basename='pentestuser')
router.register('pentestusers/self/notes/images', UploadedUserNotebookImageViewSet, basename='uploadedusernotebookimage')
router.register('pentestusers/self/notes', UserNotebookPageViewSet, basename='usernotebookpage')
router.register('projecttypes', ProjectTypeViewSet, basename='projecttype')
router.register('pentestprojects', PentestProjectViewSet, basename='pentestproject')
router.register('archivedprojects', ArchivedProjectViewSet, basename='archivedproject')
router.register('findingtemplates', FindingTemplateViewSet, basename='findingtemplate')
router.register('utils', UtilsViewSet, basename='utils')
router.register('auth', AuthViewSet, basename='auth')

user_router = NestedSimpleRouter(router, 'pentestusers', lookup='pentestuser')
user_router.register('mfa', MFAMethodViewSet, basename='mfamethod')
user_router.register('identities', AuthIdentityViewSet, basename='authidentity')
user_router.register('notifications', NotificationViewSet, basename='notification')
user_router.register('publickeys', UserPublicKeyViewSet, basename='userpublickey')

project_router = NestedSimpleRouter(router, 'pentestprojects', lookup='project')
project_router.register('sections', ReportSectionViewSet, basename='section')
project_router.register('findings', PentestFindingViewSet, basename='finding')
project_router.register('notes', ProjectNotebookPageViewSet, basename='projectnotebookpage')
project_router.register('images', UploadedImageViewSet, basename='uploadedimage')
project_router.register('files', UploadedProjectFileViewSet, basename='uploadedprojectfile')

projecttype_router = NestedSimpleRouter(router, 'projecttypes', lookup='projecttype')
projecttype_router.register('assets', UploadedAssetViewSet, basename='uploadedasset')

archivedproject_router = NestedSimpleRouter(router, 'archivedprojects', lookup='archivedproject')
archivedproject_router.register('keyparts', ArchivedProjectKeyPartViewSet, basename='archivedprojectkeypart')

# Make trailing slash in URL optional to support loading images and assets by fielname
router.trailing_slash = '/?'
project_router.trailing_slash = '/?'
projecttype_router.trailing_slash = '/?'
archivedproject_router.trailing_slash = '/?'


urlpatterns = [
    path('admin/login/', RedirectView.as_view(url='/users/self/admin/enable/')),
    path('admin/', admin.site.urls),
    re_path(r'^api/?$', RedirectView.as_view(url='/api/v1/')),
    path('api/v1/', include([
        path('', include(router.urls)),
        path('', include(user_router.urls)),
        path('', include(project_router.urls)),
        path('', include(projecttype_router.urls)),
        path('', include(archivedproject_router.urls)),

        # Async views
        path('utils/spellcheck/', SpellcheckView.as_view(), name='utils-spellcheck'),
        path('utils/spellcheck/words/', SpellcheckWordView.as_view(), name='utils-spellcheck-words'),
        path('utils/healthcheck/', HealthcheckView.as_view(), name='utils-healthcheck'),
        path('pentestprojects/<uuid:pk>/preview/', PentestProjectPreviewView.as_view(), name='pentestproject-preview'),
        path('pentestprojects/<uuid:pk>/generate/', PentestProjectGenerateView.as_view(), name='pentestproject-generate'),
        path('projecttypes/<uuid:pk>/preview/', ProjectTypePreviewView.as_view(), name='projecttype-preview'),
    ])),

    # Static files
    path('robots.txt', lambda *args, **kwargs: HttpResponse("User-Agent: *\nDisallow: /\n", content_type="text/plain")),
    
    # Fallback URL for SPA
    re_path(r'^(?!(api|admin)).*/?$', TemplateView.as_view(template_name='index.html')),
]


if settings.DEBUG:
    urlpatterns = [
        path('__debug__/', include('debug_toolbar.urls')),
    ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + urlpatterns

