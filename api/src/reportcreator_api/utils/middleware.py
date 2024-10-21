from datetime import timedelta
from urllib.parse import urlparse

from channels.security.websocket import OriginValidator, WebsocketDenier
from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware
from django.utils import cache, deprecation, timezone


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
        if request.session and request.session.session_key and \
            request.session.expire_date - timezone.now() > timedelta(seconds=request.session.get_expiry_age() / 2):
            # Extend session lifetime
            # When a session value is changed the session is updated in the DB and its lifetime is reset to SESSION_COOKIE_AGE
            # This does not affect the "Expire" attribute on the session cookie.
            # If SESSION_EXPIRE_AT_BROWSER_CLOSE=True, the Expire attribute is still unset
            request.session['tmp_extend_session_time'] = request.session.get('tmp_extend_session_time', 0) + 1


class AdminSessionMiddleware(deprecation.MiddlewareMixin):
    def process_request(self, request):
        if request.user and request.session and request.session.get('admin_permissions_enabled'):
            request.user.admin_permissions_enabled = True


class CacheControlMiddleware(deprecation.MiddlewareMixin):
    def process_response(self, request, response):
        if response.has_header('Cache-Control'):
            return response

        # Cache static files
        if request.path.startswith(settings.STATIC_URL) and response.status_code == 200 and not settings.DEBUG:
            if any(request.path.endswith(e) for e in ['.html', '.json']) or \
                (request.path.startswith(settings.STATIC_URL + 'plugins/') and '/_nuxt/' not in request.path):
                # Do not cache for long
                cache.patch_cache_control(response, public=True, max_age=2 * 60)
            else:
                # Chunk files with unique names. Can be cached for a long time
                cache.patch_cache_control(response, public=True, max_age=24 * 3600)
        else:
            # Do not cache API responses and django views
            cache.add_never_cache_headers(response)

        return response


class PermissionsPolicyMiddleware(deprecation.MiddlewareMixin):
    def process_response(self, request, response):
        response.headers['Permissions-Policy'] = ', '.join(map(lambda t: f"{t[0]}={t[1] or '()'}", settings.PERMISSIONS_POLICY.items()))
        return response


class WebsocketOriginValidatorMiddleware(OriginValidator):
    def __init__(self, application):
        super().__init__(application, allowed_origins=settings.ALLOWED_HOSTS)

    async def __call__(self, scope, receive, send):
        if '*' in self.allowed_origins:
            if self.check_origin_is_host(scope):
                return await self.application(scope, receive, send)
            else:
                denier = WebsocketDenier()
                return await denier(scope, receive, send)

        return await super().__call__(scope, receive, send)

    def check_origin_is_host(self, scope):
        """
        Check if the origin header is the same as the host header.
        If they are equal, this means that the request was sent same-origin.

        Browsers always include the Origin header when establishing websocket connections via the WebSocket API
        (except from secure contexts, such as file:// URLs where the "Origin: null" is sent).
        Non-browser clients (e.g. CLI, API clients, etc.) may not send the Origin header.
        """
        host = self.get_header(scope, 'host')
        origin = self.get_header(scope, 'origin')
        allowed_origin = f"{'https' if scope.get('scheme') == 'wss' else 'http'}://{host}"

        return origin is None or origin == allowed_origin

    @staticmethod
    def get_header(scope, name):
        return next((header[1].decode() for header in scope.get('headers', []) if header[0] == name.encode()), None)

