from collections import OrderedDict
from uuid import UUID
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import make_password
from reportcreator_api.users.models import PentestUser
from reportcreator_api.utils.utils import omit_items


class PentestUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = PentestUser
        fields = ['id', 'username', 'name', 'title_before', 'first_name', 'middle_name', 'last_name', 'title_after']


class PentestUserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = PentestUser
        fields = [
            'id', 'created', 'updated', 'last_login', 'is_active',
            'username', 'name', 'title_before', 'first_name', 'middle_name', 'last_name', 'title_after',
            'email', 'phone', 'mobile',
            'scope', 'is_superuser', 'is_designer', 'is_template_editor', 'is_user_manager', 'is_guest',
        ]
    
    def get_extra_kwargs(self):
        user = self.context['request'].user
        read_only = not (user.is_user_manager or user.is_superuser)
        return super().get_extra_kwargs() | {
            'is_superuser': {'read_only': not user.is_superuser},
            'is_user_manager': {'read_only': read_only},
            'is_designer': {'read_only': read_only},
            'is_template_editor': {'read_only': read_only},
            'is_guest': {'read_only': read_only},
            'username': {'read_only': read_only},
        }


class CreateUserSerializer(PentestUserDetailSerializer):
    class Meta(PentestUserDetailSerializer.Meta):
        fields = PentestUserDetailSerializer.Meta.fields + ['password']
        extra_kwargs = {'password': {'write_only': True}}
    
    def validate_password(self, value):
        validate_password(value, user=self.instance)
        return make_password(value)


class RelatedUserSerializer(serializers.PrimaryKeyRelatedField):
    requires_context = True

    def __init__(self, user_serializer=PentestUserSerializer, **kwargs):
        self.user_serializer=user_serializer
        super().__init__(**kwargs)

    def get_queryset(self):
        qs = PentestUser.objects.all()
        if request := self.context.get('request'):
            qs = qs.only_permitted(request.user)
        return qs

    def use_pk_only_optimization(self):
        return False

    def to_internal_value(self, data):
        if isinstance(data, dict) and 'id' in data:
            return self.get_queryset().get(pk=data['id'])
        elif isinstance(data, (str, UUID)):
            return self.get_queryset().get(pk=data)
        else:
            return data

    def to_representation(self, value):
        return self.user_serializer(value).to_representation(value)

    def get_choices(self, cutoff=None):
        queryset = self.get_queryset()
        if queryset is None:
            # Ensure that field.choices returns something sensible
            # even when accessed with a read-only field.
            return {}

        if cutoff is not None:
            queryset = queryset[:cutoff]

        return OrderedDict([(str(item.pk), self.display_value(item)) for item in queryset])


class ChangePasswordSerializer(serializers.ModelSerializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    class Meta:
        model = PentestUser
        fields = ['old_password', 'new_password']

    def validate_old_password(self, value):
        if not self.instance.check_password(value):
            raise serializers.ValidationError('Old password is not correct')
        return value

    def validate_new_password(self, value):
        validate_password(value, user=self.instance)
        return value

    def update(self, instance, validated_data):
        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance


class ResetPasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = PentestUser
        fields = ['password']
    
    def validate_password(self, value):
        validate_password(value, user=self.instance)
        return value
    
    def update(self, instance, validated_data):
        instance.set_password(validated_data['password'])
        instance.save()
        return instance
