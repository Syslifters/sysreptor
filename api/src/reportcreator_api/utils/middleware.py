from urllib.parse import urlparse
from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware


class CustomCsrfMiddleware(CsrfViewMiddleware):
    def _origin_verified(self, request):
        if super()._origin_verified(request):
            return True
        
        try:
            parsed_origin = urlparse(request.META["HTTP_ORIGIN"])
        except ValueError:
            return False
        
        # Allow skipping origin checks
        return parsed_origin.scheme + '://*' in settings.CSRF_TRUSTED_ORIGINS
