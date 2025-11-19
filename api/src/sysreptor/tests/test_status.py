import itertools

import pytest
from django.urls import reverse

from sysreptor.pentests.models import ReviewStatus
from sysreptor.tests.mock import api_client, create_finding, create_project, create_user, override_configuration, update
from sysreptor.utils.configuration import configuration


@pytest.mark.django_db()
class TestReviewStatusTransitions:
    @override_configuration(STATUS_DEFINITIONS=[
        {"id": "in-progress", "label": "In Progress"},
        {"id": "custom", "label": "Custom", "allowed_next_statuses": None},
        {"id": "finished", "label": "Finished", "allowed_next_statuses": []},
    ])
    def test_no_restrictions_when_allowed_next_statuses_not_defined(self):
        for (from_status, to_status) in itertools.combinations_with_replacement(configuration.STATUS_DEFINITIONS, 2):
            assert ReviewStatus.validate_transition(from_status['id'], to_status['id'])
        assert ReviewStatus.validate_transition('unknown', 'in-progress')
        assert ReviewStatus.validate_transition('in-progress', 'unknown')

    @pytest.mark.parametrize(('from_status', 'to_status', 'expected'), [
        # Allowed transitions
        ('in-progress', 'ready-for-review', True),
        ('ready-for-review', 'needs-improvement', True),
        ('ready-for-review', 'finished', True),
        ('needs-improvement', 'ready-for-review', True),
        # Disallowed transitions
        ('in-progress', 'finished', False),
        ('ready-for-review', 'in-progress', False),
        ('needs-improvement', 'finished', False),
        ('needs-improvement', 'in-progress', False),
        ('finished', 'ready-for-review', False),
        # Transition from unknown to any status allowed
        ('unknown', 'unknown', True),
        ('unknown', 'another-unknown', True),
        *itertools.chain(*([
            # Transition to same status always allowed
            (s, s, True),
            # Transition from unknown status always allowed
            ("unknown", s, True),
            # Transition to unknown status not allowed
            (s, "unknown", False),
            # Initial creation always allowed
            (None, s, True),
        ] for s in ['in-progress', 'ready-for-review', 'needs-improvement', 'finished'])),
    ])
    @override_configuration(STATUS_DEFINITIONS=[
        {"id": "in-progress", "label": "In Progress", "allowed_next_statuses": ["ready-for-review"]},
        {"id": "ready-for-review", "label": "Ready for Review", "allowed_next_statuses": ["needs-improvement", "finished"]},
        {"id": "needs-improvement", "label": "Needs Improvement", "allowed_next_statuses": ["ready-for-review"]},
        {"id": "finished", "label": "Finished", "allowed_next_statuses": ["finished"]},
    ])
    def test_validate_transitions(self, from_status, to_status, expected):
        assert ReviewStatus.validate_transition(from_status, to_status) == expected

    @pytest.mark.parametrize(('username', 'from_status', 'to_status', 'expected'), [
        ('user_regular', 'in-progress', 'ready-for-review', True),
        ('user_regular', 'finished', 'in-progress', False),
        ('user_regular', 'unknown', 'finished', True),
        ('user_regular', 'in-progress', 'unknown', False),
        # Admin user bypasses restrictions
        ('user_admin', 'in-progress', 'ready-for-review', True),
        ('user_admin', 'finished', 'in-progress', True),
        ('user_admin', 'unknown', 'finished', True),
        ('user_admin', 'in-progress', 'unknown', True),
    ])
    @override_configuration(STATUS_DEFINITIONS=[
        {"id": "in-progress", "label": "In Progress", "allowed_next_statuses": ["ready-for-review"]},
        {"id": "ready-for-review", "label": "Ready for Review", "allowed_next_statuses": ["needs-improvement", "finished"]},
        {"id": "needs-improvement", "label": "Needs Improvement", "allowed_next_statuses": ["ready-for-review"]},
        {"id": "finished", "label": "Finished", "allowed_next_statuses": ["finished"]},
    ])
    def test_update_status_api(self, username, from_status, to_status, expected):
        user = {
            'user_regular': create_user(username='user_regular'),
            'user_admin': create_user(username='user_admin', is_superuser=True, admin_permissions_enabled=True),
        }[username]
        client = api_client(user=user)

        project = create_project(members=[user], findings_kwargs=[])
        finding = create_finding(project=project, status=from_status)
        res_f = client.patch(reverse('finding-detail', kwargs={'project_pk': project.pk, 'id': finding.finding_id}), data={
            'status': to_status,
        })
        assert res_f.status_code == 200 if expected else 400

        section = update(project.sections.first(), status=from_status)
        res_s = client.patch(reverse('section-detail', kwargs={'project_pk': project.pk, 'id': section.section_id}), data={
            'status': to_status,
        })
        assert res_s.status_code == 200 if expected else 400

