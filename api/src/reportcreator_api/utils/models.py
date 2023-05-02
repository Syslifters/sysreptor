import itertools
import uuid
import functools
from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericRelation


class ModelDiffMixin(object):
    """
    A model mixin that tracks model fields' values and provide some useful api
    to know what fields have been changed.
    """

    def __init__(self, *args, **kwargs):
        super(ModelDiffMixin, self).__init__(*args, **kwargs)
        self.__initial = self._dict

    @property
    def diff(self):
        d1 = self.__initial
        d2 = self._dict
        diffs = [(k, (v, d2[k])) for k, v in d1.items() if v != d2[k]]
        return dict(diffs)

    @property
    def has_changed(self):
        return bool(self.diff)

    @property
    def changed_fields(self):
        return self.diff.keys()

    def get_field_diff(self, field_name):
        """
        Returns a diff for field if it's changed and None otherwise.
        """
        return self.diff.get(field_name, None)

    def clear_changed_fields(self):
        self.__initial = self._dict

    def save(self, *args, **kwargs):
        """
        Saves model and set initial state.
        """
        super(ModelDiffMixin, self).save(*args, **kwargs)
        self.clear_changed_fields()

    @property
    def _dict(self):
        diff_fields = {field.attname for field in self._meta.fields  if not isinstance(field, GenericRelation)} - self.get_deferred_fields()

        out = {}
        for f in itertools.chain(self._meta.concrete_fields, self._meta.private_fields, self._meta.many_to_many):
            if getattr(f, 'attname', None) in diff_fields:
                v = f.value_from_object(self)
                if isinstance(v, (dict, list)):
                    v = v.copy()
                out[f.attname] = v
        return out


def now():
    return timezone.now()


class BaseModel(ModelDiffMixin, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(default=now, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True
        ordering = ['-created']


def disable_for_loaddata(signal_handler):
    """
    Decorator that turns off signal handlers when loading fixture data.
    """

    @functools.wraps(signal_handler)
    def wrapper(*args, **kwargs):
        if kwargs.get('raw'):
            return
        signal_handler(*args, **kwargs)
    return wrapper

