import pytest
from pytest_django.asserts import assertNumQueries

from reportcreator_api.pentests.models import PentestFinding, PentestProject, ReviewStatus

from .mock import create_project, create_project_type


@pytest.mark.django_db()
def test_model_diff():
    finding = create_project().findings.first()

    f = PentestFinding.objects.get(id=finding.id)
    f.status = ReviewStatus.NEEDS_IMPROVEMENT
    f.update_data({'title': 'changed'})

    assert f.has_changed
    assert set(f.changed_fields) == {'status', 'custom_fields'}
    assert f.get_field_diff('status') == (finding.status, f.status)
    assert f.get_field_diff('custom_fields'), (finding.custom_fields, f.custom_fields)


@pytest.mark.django_db()
def test_diff_related():
    project_type = create_project_type()
    project_type2 = create_project_type()
    project = create_project(project_type=project_type)

    p = PentestProject.objects.get(id=project.id)
    p.project_type = project_type2
    assert p.has_changed
    assert set(p.changed_fields) == {'project_type_id'}
    assert p.get_field_diff('project_type_id') == (project_type.id, project_type2.id)


@pytest.mark.django_db()
def test_diff_deferred_fields():
    project = create_project()

    # Deferred fields should not cause DB queries
    with assertNumQueries(1):
        p = PentestProject.objects.only('id', 'readonly').get(id=project.id)

        # Changes on deferred fields are not detected
        p.name = 'changed'   # write deferred
        assert not p.has_changed
        # Changes on non-deferred fields are detected
        p.readonly = True
        assert p.has_changed
