"""
Unit tests for plugin functionality.

To run this test, execute the following command:
cd sysreptor/dev
docker compose run --rm -e ENABLED_PLUGINS=demoplugin api pytest sysreptor_plugins/demoplugin
"""

import pytest
from django.urls import reverse
from sysreptor.tests.mock import (
    api_client,
    create_user,
)

from ..apps import DemoPluginConfig
from ..models import DemoPluginModel

PLUGIN_ID = DemoPluginConfig.plugin_id
URL_NAMESPACE = DemoPluginConfig.label


@pytest.mark.django_db()
class TestDemoPluginApi:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user()
        self.client = api_client(self.user)
        self.demopluginmodel = DemoPluginModel.objects.create(name='Test')

    def test_retrieve(self):
        res = self.client.get(reverse(URL_NAMESPACE + ':demopluginmodel-detail', kwargs={'pk': self.demopluginmodel.id}))
        assert res.status_code == 200
        assert res.data['id'] == str(self.demopluginmodel.id)
        assert res.data['name'] == self.demopluginmodel.name

    def test_create(self):
        res = self.client.post(reverse(URL_NAMESPACE + ':demopluginmodel-list'), data={'name': 'New'})
        assert res.status_code == 201
        obj = DemoPluginModel.objects.get(id=res.data['id'])
        assert obj.name == 'New'

    def test_update(self):
        res = self.client.patch(reverse(URL_NAMESPACE + ':demopluginmodel-detail', kwargs={'pk': self.demopluginmodel.id}), data={'name': 'Updated'})
        assert res.status_code == 200
        self.demopluginmodel.refresh_from_db()
        assert self.demopluginmodel.name == 'Updated'

    def test_delete(self):
        res = self.client.delete(reverse(URL_NAMESPACE + ':demopluginmodel-detail', kwargs={'pk': self.demopluginmodel.id}))
        assert res.status_code == 204
        assert not DemoPluginModel.objects.filter(id=self.demopluginmodel.id).exists()
