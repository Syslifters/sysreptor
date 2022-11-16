import logging
from django.utils import timezone
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


class RequestLoggingMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        user = '<none>'
        if getattr(request, 'user', None) and not request.user.is_anonymous:
            user = request.user.username
        log.info('%s %s %d (user=%s)', request.method, request.get_full_path(), response.status_code, user)
        return response

    def process_exception(self, request, exception):
        log.exception(str(exception))
        return None

