from contextlib import contextmanager
import itertools
from typing import Any
import uuid
import functools
from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericRelation
from simple_history import models as history_models
from simple_history import signals as history_signals
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
    def __init__(self, bases=(HistoricalRecordBase,), excluded_fields=tuple(), **kwargs):
        super().__init__(bases=bases, excluded_fields=('updated', 'lock_info_data') + tuple(excluded_fields), **kwargs)

    def post_save(self, instance, created, using=None, **kwargs):
        if getattr(instance, 'skip_history_when_saving', False):
            # Allow skip_history_when_saving also for create 
            return
        if not created and not set(instance.changed_fields).intersection(map(lambda f: f.attname, instance.history.model.tracked_fields)):
            # Skip history when there were no changes
            return
        return super().post_save(instance, created, using, **kwargs)
    
    def get_extra_fields(self, model, fields):
        excluded_fields = self.excluded_fields
        def get_instance(self):
            # Override get_instance from django-simple-history to not fetch excluded fields from the current state
            # Instead they will be ignored and use the default value.
            attrs = {}
            for k, field in fields.items():
                if isinstance(field, models.ForeignKey) and field.is_cached(self):
                    attrs[k] = getattr(self, k)
                else:
                    attrs[field.attname] = getattr(self, field.attname)

            if 'updated' in excluded_fields:
                attrs['updated'] = self.history_date

            result = model(**attrs)
            setattr(result, history_models.SIMPLE_HISTORY_REVERSE_ATTR_NAME, self)
            return result

        return super().get_extra_fields(model, fields) | {
            'instance': property(get_instance),
        }


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
        history_date = history_date or getattr(HistoricalRecords.context, 'history_date', None)
        history_change_reason = history_change_reason or getattr(HistoricalRecords.context, 'history_change_reason', None)
        return history_utils.bulk_create_with_history(
            model=model, 
            objs=objs, 
            default_date=history_date, 
            default_change_reason=history_change_reason,
            **kwargs)
    else:
        return model.objects.bulk_create(objs=objs)


@transaction.atomic
def bulk_update_with_history(model, objs, fields, history_date=None, history_change_reason=None, history_prevent_cleanup=None):
    """
    Customization of simple_history.utils.bulk_update_with_history that 
    respects settings.SIMPLE_HISTORY_ENABLED, 
    sends the pre_create_historical_record signal and 
    support settings additional history model fields.
    """

    out = model.objects.bulk_update(objs=objs, fields=fields)
    if settings.SIMPLE_HISTORY_ENABLED:
        historical_records = []
        for obj in objs:
            # Skip history for unchanged objects
            if not set(obj.changed_fields).intersection(fields):
                continue
            
            historical_obj = model.history.model(
                history_type='~',
                history_date=getattr(obj, '_history_date', None) or history_date,
                history_change_reason=getattr(obj, '_history_change_reason', None) or history_change_reason,
                history_user=model.history.model.get_default_history_user(obj),
                history_prevent_cleanup=history_prevent_cleanup or False,
                **{f.attname: getattr(obj, f.attname) for f in model.history.model.tracked_fields}
            )
            history_signals.pre_create_historical_record.send(
                sender=model.history.model, 
                instance=obj,
                history_instance=historical_obj,
                history_date=historical_obj.history_date,
                history_user=historical_obj.history_user,
                history_change_reason=historical_obj.history_change_reason,
                using=None,
            )

            historical_records.append(historical_obj)
        model.history.bulk_create(historical_records)
    return out


@contextmanager
def history_context(**kwargs):
    try:
        for k, v in kwargs.items():
            setattr(HistoricalRecords.context, k, v)
        yield
    finally: 
        for k, v in kwargs.items():
            delattr(HistoricalRecords.context, k)


def bulk_delete_with_history(model, objs, history_date=None, history_change_reason=None):
    with history_context(history_date=history_date, history_change_reason=history_change_reason):
        return model.objects \
            .filter(pk__in=map(lambda o: o.pk, objs)) \
            .delete()

