from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from django.http import HttpResponse
from django.views.generic.base import TemplateView, RedirectView
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter
from reportcreator_api.api_utils.views import UtilsViewSet

from reportcreator_api.pentests.views import FindingTemplateViewSet, PentestFindingViewSet, PentestProjectViewSet, ProjectTypeViewSet, ReportSectionViewSet, UploadedAssetViewSet, UploadedImageViewSet
from reportcreator_api.users.views import PentestUserViewSet, MFAMethodViewSet, AuthViewSet


router = DefaultRouter()
router.register('pentestusers', PentestUserViewSet, basename='pentestuser')
router.register('projecttypes', ProjectTypeViewSet, basename='projecttype')
router.register('pentestprojects', PentestProjectViewSet, basename='pentestproject')
router.register('findingtemplates', FindingTemplateViewSet, basename='findingtemplate')
router.register('utils', UtilsViewSet, basename='utils')
router.register('auth', AuthViewSet, basename='auth')

user_router = NestedSimpleRouter(router, 'pentestusers', lookup='pentestuser')
user_router.register('mfa', MFAMethodViewSet, basename='mfamethod')

project_router = NestedSimpleRouter(router, 'pentestprojects', lookup='project')
project_router.register('sections', ReportSectionViewSet, basename='section')
project_router.register('findings', PentestFindingViewSet, basename='finding')
project_router.register('images', UploadedImageViewSet, basename='uploadedimage')

projecttype_router = NestedSimpleRouter(router, 'projecttypes', lookup='projecttype')
projecttype_router.register('assets', UploadedAssetViewSet, basename='uploadedasset')

# Make trailing slash in URL optional to support loading images and assets by fielname
router.trailing_slash = '/?'
project_router.trailing_slash = '/?'
projecttype_router.trailing_slash = '/?'


urlpatterns = [
    path('admin/login/', RedirectView.as_view(url=settings.LOGIN_URL)),
    path('admin/', admin.site.urls),
    re_path(r'^api/?$', RedirectView.as_view(url='/api/v1/')),
    path('api/v1/', include([
        path('', include(router.urls)),
        path('', include(user_router.urls)),
        path('', include(project_router.urls)),
        path('', include(projecttype_router.urls)),
    ])),

    path('robots.txt', lambda *args, **kwargs: HttpResponse("User-Agent: *\nDisallow: /\n", content_type="text/plain")),
    
    # Fallback URL for SPA
    re_path(r'^(?!(api|admin)).*/?$', TemplateView.as_view(template_name='index.html')),
]


if settings.DEBUG:
    urlpatterns = [
        path('__debug__/', include('debug_toolbar.urls')),
    ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + urlpatterns

