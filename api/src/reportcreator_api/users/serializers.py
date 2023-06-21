from collections import OrderedDict
from uuid import UUID
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.conf import settings

from reportcreator_api.users.models import PentestUser, MFAMethod, MFAMethodType, AuthIdentity
from reportcreator_api.utils import license


class PentestUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = PentestUser
        fields = ['id', 'username', 'name', 'title_before', 'first_name', 'middle_name', 'last_name', 'title_after', 'is_active']


class PentestUserDetailSerializer(serializers.ModelSerializer):
    is_mfa_enabled = serializers.SerializerMethodField()

    class Meta:
        model = PentestUser
        fields = [
            'id', 'created', 'updated', 'last_login', 'is_active',
            'username', 'name', 'title_before', 'first_name', 'middle_name', 'last_name', 'title_after',
            'email', 'phone', 'mobile',
            'scope', 'is_superuser', 'is_designer', 'is_template_editor', 'is_user_manager', 'is_guest', 'is_system_user', 'is_global_archiver',
            'is_mfa_enabled', 'can_login_local', 'can_login_sso',
        ]
        read_only_fields = ['is_system_user']

    def get_is_mfa_enabled(self, obj):
        if (is_mfa_enabled := getattr(obj, 'is_mfa_enabled', None)) is not None:
            return is_mfa_enabled
        return obj.mfa_methods.all().exists()
    
    def get_extra_kwargs(self):
        user = self.context['request'].user
        read_only = not (user.is_user_manager or user.is_admin)
        return super().get_extra_kwargs() | {
            'is_superuser': {'read_only': not user.is_admin},
            'is_user_manager': {'read_only': read_only},
            'is_designer': {'read_only': read_only},
            'is_template_editor': {'read_only': read_only},
            'is_guest': {'read_only': read_only},
            'is_global_archiver': {'read_only': read_only},
            'username': {'read_only': read_only},
        }


class CreateUserSerializer(PentestUserDetailSerializer):
    class Meta(PentestUserDetailSerializer.Meta):
        fields = PentestUserDetailSerializer.Meta.fields + ['password']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def get_extra_kwargs(self):
        return super().get_extra_kwargs() | {
            'password': 
                {'required': False, 'allow_null': True, 'default': None} 
                if license.is_professional() and (not settings.LOCAL_USER_AUTH_ENABLED or settings.REMOTE_USER_AUTH_ENABLED or settings.AUTHLIB_OAUTH_CLIENTS) else 
                {}
        }
    
    def validate_password(self, value):
        if value:
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
        try:
            if isinstance(data, dict) and 'id' in data:
                return self.get_queryset().get(pk=data['id'])
            elif isinstance(data, (str, UUID)):
                return self.get_queryset().get(pk=data)
            else:
                return data
        except ObjectDoesNotExist as ex:
            raise serializers.ValidationError('Invalid user') from ex

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


class MFAMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = MFAMethod
        fields = ['id', 'method_type', 'is_primary', 'name']
        read_only_fields = ['method_type']

    @transaction.atomic()
    def update(self, instance, validated_data):
        if validated_data.get('is_primary', False):
            self.instance.user.mfa_methods.update(is_primary=False)

        return super().update(instance, validated_data)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, attrs):
        try:
            user = PentestUser.objects.get(username=attrs['username'])
        except PentestUser.DoesNotExist:
            user = PentestUser()
        
        if not user.check_password(attrs['password']):
            raise serializers.ValidationError('Invalid username or password')

        return user


class MFAMethodRelatedField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return self.context['request'].user.mfa_methods.all()


class LoginMFACodeSerializer(serializers.Serializer):
    id = MFAMethodRelatedField()
    code = serializers.CharField()

    def validate(self, attrs):
        mfa_method = attrs['id']
        if not mfa_method.verify_code(attrs['code']):
            raise serializers.ValidationError('Invalid code')
        return mfa_method


class MFAMethodRegisterSerializerBase(serializers.Serializer):
    @property
    def method_type(self):
        return None

    def validate(self, attrs):
        if self.instance.method_type != self.method_type:
            raise serializers.ValidationError('Invalid MFA Method')
        if self.instance.user != self.context['user']:
            raise serializers.ValidationError('Invalid user')
        return super().validate(attrs)

    def update(self, instance, validated_data):
        instance.is_primary = self.method_type != MFAMethodType.BACKUP and not instance.user.mfa_methods.filter(is_primary=True).exists()
        instance.save()
        return instance


class MFAMethodRegisterBackupCodesSerializer(MFAMethodRegisterSerializerBase):
    method_type = MFAMethodType.BACKUP


class MFAMethodRegisterTOTPSerializer(MFAMethodRegisterSerializerBase):
    method_type = MFAMethodType.TOTP
    code = serializers.CharField()

    def validate(self, attrs):
        if not self.instance.verify_code(attrs['code']):
            raise serializers.ValidationError('Invalid code')
        return attrs


class MFAMethodRegisterFIDO2Serializer(MFAMethodRegisterSerializerBase):
    method_type = MFAMethodType.FIDO2

    def update(self, instance, validated_data):
        try:
            instance = MFAMethod.objects.create_fido2_complete(instance=instance, response=self.initial_data, save=False)
        except ValueError as ex:
            if ex.args and len(ex.args) == 1 and isinstance(ex.args[0], str):
                raise serializers.ValidationError(ex.args[0], 'fido2') from ex
            else:
                raise ex
        return super().update(instance, validated_data)


class AuthIdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthIdentity
        fields = ['id', 'created', 'updated', 'provider', 'identifier']
    
    def create(self, validated_data):
        return super().create(validated_data | {'user': self.context['user']})
    