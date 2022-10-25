from urllib.parse import urlparse
from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware, RejectRequest


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
    
    def _check_token(self, request):
        try:
            return super()._check_token(request)
        except RejectRequest as ex:
            # Disable CSRF checking if the HTTP Bearer Authorization is used for API access.
            # Browsers do not set Bearer Authorization, JS is required, therefore CSRF is not possible.
            if 'HTTP_AUTHORIZATION' in request.META and request.META['HTTP_AUTHORIZATION'].startswith('Bearer'):
                return None
            raise ex

