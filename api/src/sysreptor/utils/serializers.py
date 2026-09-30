from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers


class OptionalPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def __init__(self, **kwargs):
        super().__init__(**{'required': False, 'allow_null': True, 'default': None} | kwargs)

    def to_internal_value(self, data):
        if data is None:
            raise serializers.SkipField()
        if self.pk_field is not None:
            data = self.pk_field.to_internal_value(data)
        try:
            return self.get_queryset().get(pk=data)
        except ObjectDoesNotExist as ex:
            raise serializers.SkipField() from ex

