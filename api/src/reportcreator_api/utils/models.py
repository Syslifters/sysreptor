import itertools
import uuid
import functools
from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericRelation
from simple_history import models as history_models
from simple_history import utils as history_utils


class ModelDiffMixin(models.Model):
    """
    A model mixin that tracks model fields' values and provide some useful api
    to know what fields have been changed.
    """

    class Meta:
        abstract = True

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


class HistoricalRecordBase(models.Model):
    history_prevent_cleanup = models.BooleanField(default=False, db_index=True)

    class Meta:
        abstract = True


class HistoricalRecords(history_models.HistoricalRecords):
    def __init__(self, bases=(HistoricalRecordBase,),  **kwargs):
        super().__init__(bases=bases, **kwargs)

    def post_save(self, instance, created, using=None, **kwargs):
        if getattr(instance, 'skip_history_when_saving', False):
            # Allow skip_history_when_saving also for create 
            return
        return super().post_save(instance, created, using, **kwargs)


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


def bulk_create_with_history(model, objs, history_date=None, history_change_reason=None, **kwargs):
    if settings.SIMPLE_HISTORY_ENABLED:
        return history_utils.bulk_create_with_history(
            model=model, 
            objs=objs, 
            default_date=history_date, 
            history_change_reason=history_change_reason,
            **kwargs)
    else:
        return model.objects.bulk_create(objs=objs)


@transaction.atomic
def bulk_update_with_history(model, objs, fields, history_date=None, history_change_reason=None, history_prevent_cleanup=None, **kwargs):
    out = model.objects.bulk_update(objs=objs, fields=fields)
    if settings.SIMPLE_HISTORY_ENABLED:
        # TODO: implement: combination of bulk_update_with_history and bulk_history_create
        # support history_prevent_cleanup
        pass
    return out