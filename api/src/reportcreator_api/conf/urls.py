from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from django.http import HttpResponse
from django.views.generic.base import TemplateView, RedirectView
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from reportcreator_api.api_utils.views import SpellcheckWordView, UtilsViewSet, SpellcheckView, HealthcheckView
from reportcreator_api.pentests.views import ArchivedProjectKeyPartViewSet, ArchivedProjectViewSet, \
    FindingTemplateViewSet, FindingTemplateTranslationViewSet, UploadedTemplateImageViewSet, FindingTemplateHistoryViewSet, \
    PentestFindingViewSet, PentestProjectViewSet, ProjectNotebookPageViewSet, \
    PentestProjectPreviewView, PentestProjectGenerateView, UploadedAssetViewSet, ProjectTypeHistoryViewSet, \
    ProjectTypeViewSet, ProjectTypePreviewView, \
    ReportSectionViewSet, UploadedImageViewSet, UploadedProjectFileViewSet, UploadedUserNotebookImageViewSet, \
    UploadedUserNotebookFileViewSet, UserNotebookPageViewSet, UserPublicKeyViewSet, \
    ProjectNotebookPageExportPdfView, UserNotebookPageExportPdfView, PentestProjectHistoryViewSet
from reportcreator_api.users.views import APITokenViewSet, PentestUserViewSet, MFAMethodViewSet, AuthViewSet, AuthIdentityViewSet
from reportcreator_api.notifications.views import NotificationViewSet


router = DefaultRouter()
# Make trailing slash in URL optional to support loading images and assets by fielname
router.trailing_slash = '/?'

router.register('pentestusers', PentestUserViewSet, basename='pentestuser')
router.register('projecttypes', ProjectTypeViewSet, basename='projecttype')
router.register('pentestprojects', PentestProjectViewSet, basename='pentestproject')
router.register('archivedprojects', ArchivedProjectViewSet, basename='archivedproject')
router.register('findingtemplates', FindingTemplateViewSet, basename='findingtemplate')
router.register('utils', UtilsViewSet, basename='utils')
router.register('auth', AuthViewSet, basename='auth')

user_router = NestedSimpleRouter(router, 'pentestusers', lookup='pentestuser')
user_router.register('mfa', MFAMethodViewSet, basename='mfamethod')
user_router.register('identities', AuthIdentityViewSet, basename='authidentity')
user_router.register('apitokens', APITokenViewSet, basename='apitoken')
user_router.register('notifications', NotificationViewSet, basename='notification')
user_router.register('publickeys', UserPublicKeyViewSet, basename='userpublickey')
user_router.register('notes/images', UploadedUserNotebookImageViewSet, basename='uploadedusernotebookimage')
user_router.register('notes/files', UploadedUserNotebookFileViewSet, basename='uploadedusernotebookfile')
user_router.register('notes', UserNotebookPageViewSet, basename='usernotebookpage')

project_router = NestedSimpleRouter(router, 'pentestprojects', lookup='project')
project_router.register('sections', ReportSectionViewSet, basename='section')
project_router.register('findings', PentestFindingViewSet, basename='finding')
project_router.register('notes', ProjectNotebookPageViewSet, basename='projectnotebookpage')
project_router.register('images', UploadedImageViewSet, basename='uploadedimage')
project_router.register('files', UploadedProjectFileViewSet, basename='uploadedprojectfile')
project_router.register('history', PentestProjectHistoryViewSet, basename='projecthistory')

projecttype_router = NestedSimpleRouter(router, 'projecttypes', lookup='projecttype')
projecttype_router.register('assets', UploadedAssetViewSet, basename='uploadedasset')
projecttype_router.register('history', ProjectTypeHistoryViewSet, basename='projecttypehistory')

archivedproject_router = NestedSimpleRouter(router, 'archivedprojects', lookup='archivedproject')
archivedproject_router.register('keyparts', ArchivedProjectKeyPartViewSet, basename='archivedprojectkeypart')

template_router = NestedSimpleRouter(router, 'findingtemplates', lookup='template')
template_router.register('translations', FindingTemplateTranslationViewSet, basename='findingtemplatetranslation')
template_router.register('images', UploadedTemplateImageViewSet, basename='uploadedtemplateimage')
template_router.register('history', FindingTemplateHistoryViewSet, basename='templatehistory')


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
        path('', include(template_router.urls)),

        # Async views
        path('utils/spellcheck/', SpellcheckView.as_view(), name='utils-spellcheck'),
        path('utils/spellcheck/words/', SpellcheckWordView.as_view(), name='utils-spellcheck-words'),
        path('utils/healthcheck/', HealthcheckView.as_view(), name='utils-healthcheck'),
        path('pentestprojects/<uuid:pk>/preview/', PentestProjectPreviewView.as_view(), name='pentestproject-preview'),
        path('pentestprojects/<uuid:pk>/generate/', PentestProjectGenerateView.as_view(), name='pentestproject-generate'),
        path('projecttypes/<uuid:pk>/preview/', ProjectTypePreviewView.as_view(), name='projecttype-preview'),
        path('pentestprojects/<uuid:project_pk>/notes/<uuid:id>/export-pdf/', ProjectNotebookPageExportPdfView.as_view(), name='projectnotebookpage-export-pdf'),
        path('pentestusers/<str:pentestuser_pk>/notes/<uuid:id>/export-pdf/', UserNotebookPageExportPdfView.as_view(), name='usernotebookpage-export-pdf'),
    
        # OpenAPI schema
        path('utils/openapi/', SpectacularAPIView.as_view(), name='utils-openapi-schema'),
        path('utils/swagger-ui/', SpectacularSwaggerView.as_view(url_name='utils-openapi-schema'), name='utils-swagger-ui'),

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

