import re
from rest_framework import throttling


class ScopedUserRateThrottle(throttling.ScopedRateThrottle):
    def parse_rate(self, rate):
        """
        Given the request rate string, return a two tuple of:
        <allowed number of requests>, <period of time in seconds>
        """
        if rate is None:
            return (None, None)
        m = re.match(r'^(?P<rate>[0-9]+)/(?P<mult>[0-9]+)?(?P<period>s|m|h|d)$', rate)
        return int(m.group('rate')), {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}[m.group('period')] * int(m.group('mult') or 1)

    def get_ident(self, request):
        if request.user and not request.user.is_anonymous:
            return str(request.user.id)
        return super().get_ident()
