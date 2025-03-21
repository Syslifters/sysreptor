from django.contrib.sessions.backends.db import SessionStore as BaseDbSessionStore

from sysreptor.users.models import Session


class SessionStore(BaseDbSessionStore):
    _session_instance = None

    @classmethod
    def get_model_class(cls):
        return Session

    @property
    def expire_date(self):
        return getattr(self._session_instance, 'expire_date', None) or self.get_expiry_date()

    def load(self):
        s = self._get_session_from_db()
        self._session_instance = s
        return self.decode(s.session_data) if s else {}

    def create_model_instance(self, *args, **kwargs):
        res = super().create_model_instance(*args, **kwargs)
        self._session_instance = res
        return res
