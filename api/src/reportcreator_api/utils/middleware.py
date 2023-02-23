from datetime import timedelta
from django.conf import settings
from django.utils import timezone, cache, deprecation
from django.middleware.csrf import CsrfViewMiddleware
from whitenoise.middleware import WhiteNoiseMiddleware


class DisabledCsrfMiddleware(CsrfViewMiddleware):
    """
    Disable CSRF checks for DRF.
    CSRF is not possible because this application uses SameSite=strict for the sessionid cookie.
    """

    def process_request(self, request) -> None:
        pass

    def process_view(self, *args, **kwargs):
        pass

    def process_response(self, request, response):
        return response


class ExtendSessionMiddleware(deprecation.MiddlewareMixin):
    def process_request(self, request):
        if request.session and request.session.get_expiry_date() - timezone.now() > timedelta(request.session.get_expiry_age() / 2):
            # Extend session lifetime
            # When a session value is changed the session is updated in the DB and its lifetime is reset to SESSION_COOKIE_AGE
            # This does not affect the "Expire" attribute on the session cookie.
            # If SESSION_EXPIRE_AT_BROWSER_CLOSE=True, the Expire attribute is still unset
            request.session['tmp_extend_session_time'] = request.session.get('tmp_extend_session_time', 0) + 1


class CacheControlMiddleware(deprecation.MiddlewareMixin):
    def process_response(self, request, response):
        cache.add_never_cache_headers(response)
        return response


class PermissionsPolicyMiddleware(deprecation.MiddlewareMixin):
    def process_response(self, request, response):
        response.headers['Permissions-Policy'] = ', '.join(map(lambda t: f"{t[0]}={t[1] or '()'}", settings.PERMISSIONS_POLICY.items()))
        return response
