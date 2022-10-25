from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic.base import TemplateView, RedirectView
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from reportcreator_api.api_utils.views import UtilsViewSet

from reportcreator_api.pentests.views import FindingTemplateViewSet, PentestFindingViewSet, PentestProjectViewSet, ProjectTypeViewSet, ReportSectionViewSet, UploadedAssetViewSet, UploadedImageViewSet
from reportcreator_api.users.views import PentestUserViewSet, TokenLogoutView

router = DefaultRouter()
router.register('pentestusers', PentestUserViewSet, basename='pentestuser')
router.register('projecttypes', ProjectTypeViewSet, basename='projecttype')
router.register('pentestprojects', PentestProjectViewSet, basename='pentestproject')
router.register('findingtemplates', FindingTemplateViewSet, basename='findingtemplate')
router.register('utils', UtilsViewSet, basename='utils')

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
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    re_path(r'^api/?$', RedirectView.as_view(url='/api/v1/')),
    path('api/v1/', include([
        path('auth/', include([
            path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
            path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
            path('logout/', TokenLogoutView.as_view(), name='token_logout')
        ])),
        path('', include(router.urls)),
        path('', include(project_router.urls)),
        path('', include(projecttype_router.urls)),
    ])),
    
    # Fallback URL for SPA
    re_path('^.*/?$', TemplateView.as_view(template_name='index.html')),
]


if settings.DEBUG:
    urlpatterns = [
        path('__debug__/', include('debug_toolbar.urls')),
    ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + urlpatterns

