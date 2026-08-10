from sysreptor.pentests.models import PentestProject
from sysreptor.users.models import PentestUser
from sysreptor.utils import license
from sysreptor.utils.history import HistoricalRecords


def _clean_user(user):
    if user and getattr(user, 'is_anonymous', False):
        return None
    return user


def _resolve_user(user):
    return (
        _clean_user(user) or
        _clean_user(getattr(HistoricalRecords.context, 'history_user', None)) or
        _clean_user(getattr(getattr(HistoricalRecords.context, 'request', None), 'user', None))
    )


def audit_log(*, type, user=None, data=None, related=None):
    from sysreptor.audit.models import AuditLogEntry

    if not license.is_professional():
        return

    user = _resolve_user(user)
    data = dict(data or {})
    if user:
        data['actor_name'] = f'{user.username} ({user.name})'
    if 'related_name' not in data:
        if isinstance(related, PentestUser):
            data['related_name'] = f'{related.username} ({related.name})'
        elif isinstance(related, PentestProject):
            data['related_name'] = related.name
        else:
            data['related_name'] = str(related)

    AuditLogEntry.objects.create(
        type=type,
        actor=user,
        related=related,
        data=data,
    )
