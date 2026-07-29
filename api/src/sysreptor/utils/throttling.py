import hashlib
import re
import uuid

from rest_framework import throttling

from sysreptor.utils.utils import is_uuid


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

    def hash_ident(self, value: str) -> str:
        """
        Return a short, fixed-length hash so arbitrary input never bloats cache keys.
        """
        return hashlib.sha256(value.encode()).hexdigest()[:32]

    def get_ident(self, request):
        if self.scope in ('pwreset_sendmail', 'pwreset_check'):
            data = getattr(request, 'data', None) or {}
            if email := str(data.get('email') or '').strip().lower():
                return self.hash_ident(email)
            elif user := data.get('user'):
                if is_uuid(user):
                    # normalize UUID to canonical form
                    user = str(uuid.UUID(user))
                return self.hash_ident(user)
        if request.user and request.user.is_authenticated:
            return self.hash_ident(str(request.user.id))
        return super().get_ident(request)

    def get_cache_key(self, request, view):
        """Always use get_ident so scoped keys (e.g. email) are not replaced by user.pk."""
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request),
        }
