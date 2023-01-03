from django.contrib.sessions.backends.db import SessionStore as BaseDbSessionStore
from reportcreator_api.users.models import Session


class SessionStore(BaseDbSessionStore):
    @classmethod
    def get_model_class(cls):
        return Session
    
