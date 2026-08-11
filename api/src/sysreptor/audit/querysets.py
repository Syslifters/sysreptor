from collections import defaultdict

from django.apps import apps
from django.db import models
from django.db.models import Prefetch
from django.db.models.query import prefetch_related_objects


class AuditLogEntryQuerySet(models.QuerySet):
    def _prefetch_related_objects(self):
        related = False
        others = []
        for lookup in self._prefetch_related_lookups:
            key = lookup.prefetch_through if isinstance(lookup, Prefetch) else lookup
            if key == 'related' or key.startswith('related__'):
                related = True
            else:
                others.append(lookup)

        if related and self._result_cache and isinstance(self._result_cache[0], self.model):
            self._prefetch_related_instances(self._result_cache)

        if others:
            prefetch_related_objects(self._result_cache, *others)

        self._prefetch_done = True

    def _prefetch_related_instances(self, entries):
        by_ct = defaultdict(set)
        for e in entries:
            if e.content_type and e.object_id:
                by_ct[e.content_type].add(e.object_id)

        related_map = {}
        for ct, ids in by_ct.items():
            try:
                app_label, model = ct.split('.', 1)
                Model = apps.get_model(app_label, model)
            except (ValueError, LookupError):
                continue
            for obj in Model.objects.filter(pk__in=ids):
                related_map[(ct, obj.pk)] = obj

        for e in entries:
            key = (e.content_type, e.object_id) if e.content_type and e.object_id else None
            e._related_cache = related_map.get(key) if key else None


class AuditLogEntryManager(models.Manager.from_queryset(AuditLogEntryQuerySet)):
    pass
