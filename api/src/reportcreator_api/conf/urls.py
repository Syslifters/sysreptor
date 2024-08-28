from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path, re_path
from django.views.generic.base import RedirectView, TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerSplitView
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter

from reportcreator_api.api_utils.views import UtilsViewSet
from reportcreator_api.notifications.views import NotificationViewSet
from reportcreator_api.pentests.collab.fallback import ConsumerHttpFallbackView
from reportcreator_api.pentests.consumers import (
    ProjectNotesConsumer,
    ProjectReportingConsumer,
    SharedProjectNotesPublicConsumer,
    UserNotesConsumer,
)
from reportcreator_api.pentests.views import (
    ArchivedProjectKeyPartViewSet,
    ArchivedProjectViewSet,
    CommentAnswerViewSet,
    CommentViewSet,
    FindingTemplateHistoryViewSet,
    FindingTemplateTranslationViewSet,
    FindingTemplateViewSet,
    PentestFindingViewSet,
    PentestProjectHistoryViewSet,
    PentestProjectViewSet,
    ProjectNotebookPageViewSet,
    ProjectNoteShareInfoPublicViewSet,
    ProjectNoteShareInfoViewSet,
    ProjectTypeHistoryViewSet,
    ProjectTypeViewSet,
    ReportSectionViewSet,
    SharedProjectNotePublicViewSet,
    UploadedAssetViewSet,
    UploadedImageViewSet,
    UploadedProjectFileViewSet,
    UploadedTemplateImageViewSet,
    UploadedUserNotebookFileViewSet,
    UploadedUserNotebookImageViewSet,
    UserNotebookPageViewSet,
    UserPublicKeyViewSet,
)
from reportcreator_api.users.views import (
    APITokenViewSet,
    AuthIdentityViewSet,
    AuthViewSet,
    MFAMethodViewSet,
    PentestUserViewSet,
)

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
router.register('shareinfos', ProjectNoteShareInfoPublicViewSet, basename='shareinfopublic')

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
project_router.register('comments', CommentViewSet, basename='comment')
project_router.register('images', UploadedImageViewSet, basename='uploadedimage')
project_router.register('files', UploadedProjectFileViewSet, basename='uploadedprojectfile')
project_router.register('history', PentestProjectHistoryViewSet, basename='pentestprojecthistory')

comment_router = NestedSimpleRouter(project_router, 'comments', lookup='comment')
comment_router.register('answers', CommentAnswerViewSet, basename='commentanswer')

projectnotes_router = NestedSimpleRouter(project_router, 'notes', lookup='note')
projectnotes_router.register('shareinfos', ProjectNoteShareInfoViewSet, basename='shareinfo')

projecttype_router = NestedSimpleRouter(router, 'projecttypes', lookup='projecttype')
projecttype_router.register('assets', UploadedAssetViewSet, basename='uploadedasset')
projecttype_router.register('history', ProjectTypeHistoryViewSet, basename='projecttypehistory')

archivedproject_router = NestedSimpleRouter(router, 'archivedprojects', lookup='archivedproject')
archivedproject_router.register('keyparts', ArchivedProjectKeyPartViewSet, basename='archivedprojectkeypart')

template_router = NestedSimpleRouter(router, 'findingtemplates', lookup='template')
template_router.register('translations', FindingTemplateTranslationViewSet, basename='findingtemplatetranslation')
template_router.register('images', UploadedTemplateImageViewSet, basename='uploadedtemplateimage')
template_router.register('history', FindingTemplateHistoryViewSet, basename='findingtemplatehistory')

shareinfo_router = NestedSimpleRouter(router, 'shareinfos', lookup='shareinfo')
shareinfo_router.register('notes', SharedProjectNotePublicViewSet, basename='sharednote')


urlpatterns = [
    path('admin/login/', RedirectView.as_view(url='/users/self/admin/enable/', query_string=True)),
    path('admin/', admin.site.urls),
    re_path(r'^api/?$', RedirectView.as_view(url='/api/v1/')),
    path('api/v1/', include([
        path('', include(
            router.urls +
            user_router.urls +
            project_router.urls +
            comment_router.urls +
            projectnotes_router.urls +
            projecttype_router.urls +
            archivedproject_router.urls +
            template_router.urls +
            shareinfo_router.urls,
        )),

        # OpenAPI schema
        path('utils/openapi/', SpectacularAPIView.as_view(), name='utils-openapi-schema'),
        path('utils/swagger-ui/', SpectacularSwaggerSplitView.as_view(url_name='utils-openapi-schema'), name='utils-swagger-ui'),

    ])),

    # Websocket HTTP fallback
    path('ws/pentestprojects/<uuid:project_pk>/reporting/fallback/', ConsumerHttpFallbackView.as_view(consumer_class=ProjectReportingConsumer), name='projectreporting-fallback'),
    path('ws/pentestprojects/<uuid:project_pk>/notes/fallback/', ConsumerHttpFallbackView.as_view(consumer_class=ProjectNotesConsumer), name='projectnotebookpage-fallback'),
    path('ws/pentestusers/<str:pentestuser_pk>/notes/fallback/', ConsumerHttpFallbackView.as_view(consumer_class=UserNotesConsumer), name='usernotebookpage-fallback'),
    path('ws/shareinfos/<uuid:shareinfo_pk>/notes/fallback/', ConsumerHttpFallbackView.as_view(consumer_class=SharedProjectNotesPublicConsumer), name='sharednote-fallback'),

    # Static files
    path('robots.txt', lambda *args, **kwargs: HttpResponse("User-Agent: *\nDisallow: /\n", content_type="text/plain")),

    # Fallback URL for SPA
    re_path(r'^(?!(api|admin)).*/?$', TemplateView.as_view(template_name='index.html')),
]


websocket_urlpatterns = [
    path('ws/pentestprojects/<uuid:project_pk>/reporting/', ProjectReportingConsumer.as_asgi(), name='projectreporting-ws'),
    path('ws/pentestprojects/<uuid:project_pk>/notes/', ProjectNotesConsumer.as_asgi(), name='projectnotebookpage-ws'),
    path('ws/pentestusers/<str:pentestuser_pk>/notes/', UserNotesConsumer.as_asgi(), name='usernotebookpage-ws'),
    path('ws/shareinfos/<uuid:shareinfo_pk>/notes/', SharedProjectNotesPublicConsumer.as_asgi(), name='sharednote-ws'),
]


if settings.DEBUG:
    urlpatterns = [
        path('__debug__/', include('debug_toolbar.urls')),
    ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + urlpatterns

