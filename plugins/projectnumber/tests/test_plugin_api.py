import contextlib

import pytest
from django.apps import apps
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

from ..app import ProjectNumberPluginConfig
from ..models import ProjectNumber


@contextlib.contextmanager
def override_projectnumber_settings(**kwargs):
    app = apps.get_app_config(ProjectNumberPluginConfig.label)
    old_settings = app.settings
    print(kwargs)
    try:
        app.settings |= kwargs
        yield
    finally:
        app.settings = old_settings


@pytest.mark.django_db
class TestProjectNumberPlugin:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user()
        self.client = api_client(self.user)

    @pytest.mark.parametrize(
        "template, context, expected",
        [
            ("{{ project_number }}", {"project_number": 1}, "1"),
            ("Project No: {{ project_number }}", {"project_number": 1}, "Project No: 1"),
            ("R{% now 'y' %}-{{project_number|stringformat:'04d'}}", {"project_number": 1}, "R24-0001"),
            ("{% now 'Y' %}-{{project_number|stringformat:'04d'}}", {"project_number": 1}, "2024-0001"),
            ("Prefix-{% now 'y' %}{% now 'm' %}{{project_number|stringformat:'04d'}}-Suffix", {"project_number": 1}, "Prefix-24110001-Suffix"),
            ("{{ 1000|add:project_number }}", {"project_number": 1}, "1001"),
        ]
    )
    def test_on_project_saved(self, template, context, expected):
        # Override settings to use the custom template
        with override_projectnumber_settings(PLUGIN_PROJECTNUMBER_TEMPLATE=template):
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
                                ]
                            )
                        ),
                    }
                ]
            )

            # Create project
            project = create_project(project_type=project_type, members=[self.user])
            section = project.sections.get(section_id='project_number')

            assert section.data.get('project_number') == expected

            # Check project counter increment
            counter.refresh_from_db()
            assert counter.current_id == context['project_number']

    @pytest.mark.parametrize("template, context", [
        ("P{{ project_number|stringformat:'04d' }}{% random_number 5 23|stringformat:'02d' %}", {"project_number": 1}),
    ])
    def test_template_with_random_suffix(self, template, context):
        # Override settings for random number suffix template
        with override_projectnumber_settings(PLUGIN_PROJECTNUMBER_TEMPLATE=template):
            # Create project and validate random suffix
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
                                ]
                            )
                        ),
                    }
                ]
            )
            project = create_project(project_type=project_type, members=[self.user])
            section = project.sections.get(section_id='project_number')

            rendered = section.data.get('project_number')
            assert rendered.startswith(f"P{context['project_number']:04d}")

            # Validate random suffix
            random_suffix = int(rendered[-2:])
            assert 5 <= random_suffix <= 23
