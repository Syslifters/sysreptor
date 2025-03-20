from unittest import mock

import pytest
from django.core.management import call_command
from django.template.defaultfilters import date
from django.template.defaulttags import NowNode
from django.utils import dateparse
from sysreptor.tests.mock import (
    api_client,
    create_project,
    create_project_type,
    create_user,
    override_configuration,
)
from sysreptor.utils.fielddefinition.types import (
    FieldDefinition,
    StringField,
    serialize_field_definition,
)

from ..management.commands import resetprojectnumber
from ..models import ProjectNumber


class MockNowNode(NowNode):
    def render(self, context):
        now = dateparse.parse_datetime('2024-11-27T12:21:30Z')
        return date(now, self.format_string)


@pytest.mark.django_db()
class TestProjectNumberPlugin:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user()
        self.client = api_client(self.user)

    @pytest.mark.parametrize(('template', 'expected'), [
        ("{{ project_number }}", "1"),
        ("Project No: {{ project_number }}", "Project No: 1"),
        ("R{% now 'y' %}-{{project_number|stringformat:'04d'}}", "R24-0001"),
        ("{% now 'Y' %}-{{project_number|stringformat:'04d'}}", "2024-0001"),
        ("Prefix-{% now 'y' %}{% now 'm' %}{{project_number|stringformat:'04d'}}-Suffix", "Prefix-24110001-Suffix"),
        ("{{ 1000|add:project_number }}", "1001"),
        ("P{{ project_number|stringformat:'04d' }}{% random_number 5 23|stringformat:'02d' %}", "P000117"),
    ])
    def test_on_project_saved(self, template, expected):
        # Override settings to use the custom template
        with override_configuration(PLUGIN_PROJECTNUMBER_TEMPLATE=template), \
            mock.patch('django.template.defaulttags.NowNode', new=MockNowNode), \
            mock.patch('random.randint', return_value=17):

            # Initialize project counter
            counter, _ = ProjectNumber.objects.get_or_create(pk=1)
            assert counter.current_id == 0

            # Create Project Type with custom template
            project_type = create_project_type(
                report_sections=[
                    {
                        'id': 'project_number',
                        'label': 'Project Counter',
                        'fields': serialize_field_definition(
                            FieldDefinition(
                                fields=[
                                    StringField(
                                        id='project_number',
                                        label='Project Counter',
                                        required=True,
                                    ),
                                ],
                            ),
                        ),
                    },
                ],
            )

            # Create project
            project = create_project(project_type=project_type, members=[self.user])
            section = project.sections.get(section_id='project_number')

            assert section.data.get('project_number') == expected

            # Check project counter increment
            counter.refresh_from_db()
            assert counter.current_id == 1

    def test_command_resetprojectnumber(self):
        # Reset project counter to a specific value
        call_command(resetprojectnumber.Command(), '10')
        counter = ProjectNumber.objects.get(pk=1)
        assert counter.current_id == 10

        # Reset to 0
        call_command(resetprojectnumber.Command())
        counter.refresh_from_db()
        assert counter.current_id == 0
