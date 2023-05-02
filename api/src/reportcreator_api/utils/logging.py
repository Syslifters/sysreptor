import logging
from django.utils import timezone, deprecation
from django.utils.functional import wraps


log = logging.getLogger()


def log_timing(fn):
    @wraps(fn)
    def inner(*args, **kwargs):
        start_time = timezone.now()
        out = fn(*args, **kwargs)
        timing = timezone.now() - start_time     
        log.info(f'Function {fn.__name__} took {timing}')
        return out
    return inner


class RequestLoggingMiddleware(deprecation.MiddlewareMixin):
    def should_log(self, request, response):
        # Do not log healthchecks
        return request.resolver_match and request.resolver_match.url_name not in ['utils-healthcheck']

    def process_response(self, request, response):
        if self.should_log(request, response):
            user = '<none>'
            if getattr(request, 'user', None) and not request.user.is_anonymous:
                user = request.user.username
            log.info('%s %s %d (user=%s)', request.method, request.get_full_path(), response.status_code, user)
        return response

    def process_exception(self, request, exception):
        log.exception(str(exception))
        return None

