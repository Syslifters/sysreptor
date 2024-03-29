from contextlib import contextmanager

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from simple_history import manager as history_manager
from simple_history import models as history_models
from simple_history import signals as history_signals

from reportcreator_api.archive.crypto.fields import EncryptedField


class HistoricalRecordBase(models.Model):
    history_prevent_cleanup = models.BooleanField(default=False, db_index=True)
    history_title = EncryptedField(base_field=models.TextField(blank=True, null=True), null=True)

    class Meta:
        abstract = True


class HistoricalRecords(history_models.HistoricalRecords):
    def __init__(self, excluded_fields=tuple(), **kwargs):
        super().__init__(
            bases=[HistoricalRecordBase],
            history_change_reason_field=EncryptedField(base_field=models.TextField(blank=True, null=True), null=True),
            excluded_fields=('updated', 'lock_info_data') + tuple(excluded_fields),
            **kwargs
        )

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

    def get_history_user(self, instance):
        if hasattr(instance, '_history_user'):
            return instance._history_user
        elif hasattr(self.context, 'history_user'):
            return self.context.history_user
        else:
            return super().get_history_user(instance)


class HistoricalQuerySet(history_manager.HistoricalQuerySet):
    def as_instances(self):
        # Same as original as_instances, but also return deleted instances if deleted.history_date == current as_of filter
        if not self._as_instances:
            result = self.exclude(models.Q(history_type="-") & ~models.Q(history_date=self._as_of))
            result._as_instances = True
        else:
            result = self._clone()
        return result


class HistoryManager(history_manager.HistoryManager):
    def as_of(self, date):
        # Same as original as_instances, but also return deleted instances if deleted.history_date == current as_of filter
        queryset = self.get_queryset().filter(history_date__lte=date)
        if not self.instance:
            if isinstance(queryset, HistoricalQuerySet):
                queryset._as_of = date
            queryset = queryset.latest_of_each().as_instances()
            return queryset

        try:
            # historical records are sorted in reverse chronological order
            history_obj = queryset[0]
        except IndexError as ex:
            raise self.instance.DoesNotExist(
                "%s had not yet been created." % self.instance._meta.object_name
            ) from ex
        if history_obj.history_type == "-" and history_obj.history_date != date:
            raise self.instance.DoesNotExist(
                "%s had already been deleted." % self.instance._meta.object_name
            )
        result = history_obj.instance
        historic = getattr(result, history_manager.SIMPLE_HISTORY_REVERSE_ATTR_NAME)
        historic._as_of = date
        return result


@transaction.atomic
def bulk_create_with_history(model, objs, history_date=None, history_change_reason=None, **kwargs):
    out = model.objects.bulk_create(objs=objs)

    if settings.SIMPLE_HISTORY_ENABLED and hasattr(model, 'history'):
        bulk_create_history(
            model,
            objs=objs,
            history_type='+',
            history_date=history_date,
            history_change_reason=history_change_reason,
            history_prevent_cleanup=True
        )

    return out


@transaction.atomic
def bulk_update_with_history(model, objs, fields, history_date=None, history_change_reason=None, history_prevent_cleanup=None):
    """
    Customization of simple_history.utils.bulk_update_with_history that
    respects settings.SIMPLE_HISTORY_ENABLED,
    sends the pre_create_historical_record signal and
    support settings additional history model fields.
    """
    objs = list(objs)

    out = model.objects.bulk_update(objs=objs, fields=fields)
    if settings.SIMPLE_HISTORY_ENABLED:
        bulk_create_history(
            model,
            objs=filter(lambda obj: set(obj.changed_fields).intersection(fields), objs),
            history_type='~',
            history_date=history_date,
            history_change_reason=history_change_reason,
            history_prevent_cleanup=history_prevent_cleanup
        )
    return out


def bulk_create_history(model, objs, history_type=None, history_date=None, history_change_reason=None, history_prevent_cleanup=None):
    if not settings.SIMPLE_HISTORY_ENABLED:
        return

    historical_records = []
    for obj in objs:
        historical_obj = model.history.model(
            history_type=history_type or '~',
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


@contextmanager
def history_context(override_existing=False, history_date=None, **kwargs):
    """
    Set history context information such as history_date, history_change_reason, history_prevent_cleanup, etc.
    If override_existing is False, context information set in an outer history_context() call will not be overwritten and only new infos will be added.
    """
    kwargs = {
        'history_date': history_date or timezone.now()
    } | kwargs
    restore_map = {}
    try:
        for k, v in kwargs.items():
            if hasattr(HistoricalRecords.context, k):
                restore_map[k] = getattr(HistoricalRecords.context, k)
                if not override_existing:
                    continue
            setattr(HistoricalRecords.context, k, v)
        yield
    finally:
        for k in kwargs.keys():
            if k in restore_map:
                setattr(HistoricalRecords.context, k, restore_map[k])
            else:
                delattr(HistoricalRecords.context, k)


def bulk_delete_with_history(model, objs, history_date=None, history_change_reason=None):
    with history_context(history_date=history_date, history_change_reason=history_change_reason):
        return model.objects \
            .filter(pk__in=map(lambda o: o.pk, objs)) \
            .delete()


def merge_with_previous_history(instance):
    if not settings.SIMPLE_HISTORY_ENABLED:
        return
    h = instance.history.all().first()
    if not h:
        return

    for f in instance.__class__.history.model.tracked_fields:
        setattr(h, f.attname, getattr(instance, f.attname))
    h.save()

