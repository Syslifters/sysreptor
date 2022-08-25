from collections import OrderedDict
from uuid import UUID
from rest_framework import serializers
from reportcreator_api.users.models import PentestUser


class PentestUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = PentestUser
        fields = [
            'id', 'created', 'updated', 
            'username', 'is_superuser', 'password',
            'name', 'title_before', 'first_name', 'middle_name', 'last_name', 'title_after',
            'email', 'phone']
        extra_kwargs = {'password': {'write_only': True}}


class RelatedUserSerializer(serializers.PrimaryKeyRelatedField):
    queryset = PentestUser.objects.filter(is_active=True)

    def to_internal_value(self, data):
        if isinstance(data, dict) and 'id' in data:
            return self.queryset.get(pk=data['id'])
        elif isinstance(data, (str, UUID)):
            return self.queryset.get(pk=data)
        else:
            return data

    def to_representation(self, value):
        return PentestUserSerializer(value).to_representation(value)

    def get_choices(self, cutoff=None):
        queryset = self.get_queryset()
        if queryset is None:
            # Ensure that field.choices returns something sensible
            # even when accessed with a read-only field.
            return {}

        if cutoff is not None:
            queryset = queryset[:cutoff]

        return OrderedDict([(str(item.pk), self.display_value(item)) for item in queryset])

