from datetime import timedelta
from urllib.parse import urlparse
from django.conf import settings
from django.utils import timezone, cache, deprecation
from django.middleware.csrf import CsrfViewMiddleware
from whitenoise.middleware import WhiteNoiseMiddleware


class CustomCsrfMiddleware(CsrfViewMiddleware):
    def process_view(self, request, *args, **kwargs):
        # Skip CSRF checks for requests that cannot be sent cross-origin without a preflight request
        if request.content_type not in ['application/x-www-form-urlencoded', 'multipart/form-data', 'text/plain', ''] or \
           request.method != 'POST':
            return None

        return super().process_view(request, *args, **kwargs)
    
    def _origin_verified(self, request):
        if super()._origin_verified(request):
            return True
        
        try:
            parsed_origin = urlparse(request.META["HTTP_ORIGIN"])
        except ValueError:
            return False
        
        # Allow skipping origin checks
        return parsed_origin.scheme + '://*' in settings.CSRF_TRUSTED_ORIGINS



class ExtendSessionMiddleware(deprecation.MiddlewareMixin):
    def process_request(self, request):
        if request.session and request.session.get_expiry_date() - timezone.now() > timedelta(request.session.get_expiry_age() / 2):
            # Extend session lifetime
            # When a session value is changed the session is updated in the DB and its lifetime is reset to SESSION_COOKIE_AGE
            # This does not affect the "Expire" attribute on the session cookie.
            # If SESSION_EXPIRE_AT_BROWSER_CLOSE=True, the Expire attribute is still unset
            request.session['tmp_extend_session_time'] = request.session.get('tmp_extend_session_time', 0) + 1


class AdminSessionMiddleware(deprecation.MiddlewareMixin):
    def process_request(self, request):
        if request.user and request.session and request.session.get('admin_permissions_enabled'):
            setattr(request.user, 'admin_permissions_enabled', True)


class CacheControlMiddleware(deprecation.MiddlewareMixin):
    def process_response(self, request, response):
        cache.add_never_cache_headers(response)
        return response


class PermissionsPolicyMiddleware(deprecation.MiddlewareMixin):
    def process_response(self, request, response):
        response.headers['Permissions-Policy'] = ', '.join(map(lambda t: f"{t[0]}={t[1] or '()'}", settings.PERMISSIONS_POLICY.items()))
        return response
