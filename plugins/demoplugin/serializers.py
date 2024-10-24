from rest_framework import serializers

from .models import DemoPluginModel


class DemoPluginModelSerializer(serializers.ModelSerializer):
    """
    Serializers specify how to convert model instances into JSON and vice versa.
    See: https://www.django-rest-framework.org/api-guide/serializers/
         https://www.django-rest-framework.org/api-guide/fields/
    """

    class Meta:
        model = DemoPluginModel
        fields = ['id', 'created', 'updated', 'name']

