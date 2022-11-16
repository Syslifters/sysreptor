from django.db.models import OneToOneRel, OneToOneField, ForeignObject
from django.db.models.fields.related_descriptors import ReverseOneToOneDescriptor
from django.db.models.fields.related import RelatedField
from django.contrib.contenttypes.fields import GenericRelation, GenericRel, GenericForeignKey


class GenericOneToOneForeignKey(GenericForeignKey):
    pass


class GenericOneToOneRel(GenericRel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.multiple = False


class GenericOneToOneRelation(GenericRelation):
    one_to_many = False
    many_to_one = False
    one_to_one = True
    rel_class = GenericOneToOneRel

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.multiple = False

    def get_internal_type(self) -> str:
        return OneToOneField.__name__
        # return None

    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        setattr(cls, name, ReverseGenericOneToOneDescriptor(self))

    def get_accessor_name(self):
        return '<unknown>'


class ReverseGenericOneToOneDescriptor(ReverseOneToOneDescriptor):
    def __get__(self, instance, cls=None):
        if instance is None:
            return self

        # The related instance is loaded from the database and then cached
        # by the field on the model instance state. It can also be pre-cached
        # by the forward accessor (ForwardManyToOneDescriptor).
        try:
            rel_obj = self.related.get_cached_value(instance)
        except KeyError:
            related_pk = instance.pk
            if related_pk is None:
                rel_obj = None
            else:
                filter_args = {
                    self.related.content_type_field_name: self.related.get_content_type(),
                    self.related.object_id_field_name: related_pk,
                }
                try:
                    rel_obj = self.get_queryset(instance=instance).get(**filter_args)
                except self.related.related_model.DoesNotExist:
                    rel_obj = None
            self.related.set_cached_value(instance, rel_obj)

        return rel_obj
    
    def __set__(self, instance, value):
        if value is None:
            # Update the cached related instance (if any) & clear the cache.
            # Following the example above, this would be the cached
            # ``restaurant`` instance (if any).
            rel_obj = self.related.get_cached_value(instance, default=None)
            if rel_obj is not None:
                # Remove the ``restaurant`` instance from the ``place``
                # instance cache.
                self.related.delete_cached_value(instance)
                # Set the ``place`` field on the ``restaurant``
                # instance to None.
                setattr(rel_obj, self.related.name, None)
        elif not isinstance(value, self.related.related_model):
            # An object must be an instance of the related class.
            raise ValueError(
                'Cannot assign "%r": "%s.%s" must be a "%s" instance.'
                % (
                    value,
                    instance._meta.object_name,
                    self.related.get_accessor_name(),
                    self.related.related_model._meta.object_name,
                )
            )
        else:
            # Set the related instance cache used by __get__ to avoid an SQL query
            # when accessing the attribute we just set.
            self.related.set_cached_value(instance, value)

