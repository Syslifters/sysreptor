"""
Unit tests for plugin functionality.

To run this test, execute the following command:
cd sysreptor/dev
docker compose run --rm -e ENABLED_PLUGINS=projectnumber api pytest sysreptor_plugins/projectnumber
"""


import pytest
from reportcreator_api.pentests.customfields.types import (
    FieldDefinition,
    StringField,
    serialize_field_definition,
)
from reportcreator_api.tests.mock import (
    api_client,
    create_project,
    create_project_type,
    create_user,
)

from ..models import ProjectNumber


@pytest.mark.django_db
class TestOnProjectSaved:
    def test_on_project_saved(self):
        # Check if the counter is correctly initialized 
        counter, _ = ProjectNumber.objects.get_or_create(pk=1)
        assert counter.current_id == 0
        
        # Create Project
        self.user = create_user()
        self.client = api_client(self.user)
        self.project_type = create_project_type(report_sections=[{
            'id': 'project_number',
            'label': 'Project Counter',
            'fields': serialize_field_definition(FieldDefinition(fields=[
                StringField(id='project_number', label='Project Counter', required=True, default='**TODO: write executive summary**'),
            ])),
        }])
        
        self.project = create_project(project_type=self.project_type, members=[self.user])
        self.section = self.project.sections.get(section_id='project_number')
        assert self.section.data.get('project_number') == '1'

        
        # Assert Project Coutner is correctly incremented
        counter.refresh_from_db()
        assert counter.current_id == 1

