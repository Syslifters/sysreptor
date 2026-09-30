from django.contrib.auth import SESSION_KEY
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

    def create_model_instance(self, data):
        res = super().create_model_instance(data)
        res.user_id = data.get(SESSION_KEY) or None
        # Django rebuilds a new model instance on every save; keep id/created for updates.
        existing = self._session_instance
        key_hash = Session.hash_session_key(res.session_key)
        if existing is None or getattr(existing, 'session_key_hash', None) != key_hash:
            existing = Session.objects.filter(session_key_hash=key_hash).first()
        if existing is not None:
            res.pk = existing.pk
            res.created = existing.created
        self._session_instance = res
        return res
