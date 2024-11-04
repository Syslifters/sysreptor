import logging
import time

from asgiref.sync import iscoroutinefunction
from django.utils import deprecation
from django.utils.functional import wraps

from reportcreator_api.utils.utils import get_key_or_attr

log = logging.getLogger()


def format_timing(timing: float):
    return f'{timing:.2f}s'


def log_timing(log_start=False, log_detailed_timings=False):
    def wrapper(fn):
        def before(fn):
            if log_start:
                log.info(f'Function {fn.__name__} started')
            start_time = time.perf_counter()
            return start_time

        def after(fn, result, start_time):
            elapsed = time.perf_counter() - start_time
            log_msg = f'Function {fn.__name__} took {format_timing(elapsed)}'
            if log_detailed_timings and (timings := get_key_or_attr(result, 'timings')) and isinstance(timings, dict):
                timings_formatted = []
                for k, t in timings.items():
                    timings_formatted.append(f'{k}={format_timing(t)}')

                log_msg += f" ({', '.join(timings_formatted)})"
            log.info(log_msg)

        @wraps(fn)
        def inner_sync(*args, **kwargs):
            start_time = before(fn)
            result = None
            try:
                result = fn(*args, **kwargs)
                return result
            finally:
                after(fn, result=result, start_time=start_time)

        async def inner_async(*args, **kwargs):
            start_time = before(fn)
            result = None
            try:
                result = await fn(*args, **kwargs)
                return result
            finally:
                after(fn, result=result, start_time=start_time)

        return inner_async if iscoroutinefunction(fn) else inner_sync
    return wrapper


class RequestLoggingMiddleware(deprecation.MiddlewareMixin):
    def should_log(self, request, response):
        # Do not log healthchecks
        return request.resolver_match and request.resolver_match.url_name not in ['utils-healthcheck', 'publicutils-healthcheck']

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

