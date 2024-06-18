from datetime import timedelta

import pytest
from django.test import override_settings

from reportcreator_api.pentests.customfields.utils import HandleUndefinedFieldsOptions, ensure_defined_structure
from reportcreator_api.pentests.models import CommentStatus, ReviewStatus
from reportcreator_api.tests.mock import (
    create_comment,
    create_finding,
    create_project,
    create_project_type,
    create_user,
)
from reportcreator_api.utils.error_messages import ErrorMessage, MessageLevel, MessageLocationInfo, MessageLocationType

pytestmark = pytest.mark.django_db


def assertContainsCheckResults(actual, expected):
    for e in expected:
        for a in actual:
            if e.message == a.message and e.location.type == a.location.type and e.location.id == a.location.id and e.location.path == a.location.path:
                break
        else:
            pytest.fail(f'{e} not in check results')


def assertNotContainsCheckResults(actual, expected):
    for e in expected:
        for a in actual:
            if e.message == a.message and e.location.type == a.location.type and e.location.id == a.location.id and e.location.path == a.location.path:
                pytest.fail(f'{e} in check results')


def set_all_required(definiton, required):
    if definiton.get('type'):
        definiton['required'] = required
        if definiton['type'] == 'object':
            set_all_required(definiton['properties'], required)
        elif definiton['type'] == 'list':
            set_all_required(definiton['items'], required)
    elif isinstance(definiton, dict):
        for d in definiton.values():
            set_all_required(d, required)


def test_check_todo():
    todo_fields = {
        'field_string': 'TODO: content',
        'field_markdown': 'Multiline markdown \nwith ![image](To-do) in markdown\n\n* item1\n* TODO: more items',
        'field_list': ['item1', 'ToDo: more items'],
        'field_object': {'nested1': 'nested todo in object'},
        'field_list_objects': [{'nested1': 'TODO'}],
    }
    todo_field_paths = ['field_string', 'field_markdown', 'field_list[1]',
                        'field_object.nested1', 'field_list_objects[0].nested1']
    project_type = create_project_type()
    project = create_project(
        project_type=project_type,
        report_data=ensure_defined_structure(value=todo_fields, definition=project_type.report_fields_obj),
    )
    finding = create_finding(
        project=project,
        data=ensure_defined_structure(value=todo_fields, definition=project_type.finding_fields_obj),
    )

    assertContainsCheckResults(project.perform_checks(), [
        ErrorMessage(level=MessageLevel.WARNING, message='Unresolved TODO', location=MessageLocationInfo(
            type=MessageLocationType.SECTION, id='other', path=p))
        for p in todo_field_paths
    ] + [
        ErrorMessage(level=MessageLevel.WARNING, message='Unresolved TODO', location=MessageLocationInfo(
            type=MessageLocationType.FINDING, id=finding.finding_id, path=p))
        for p in todo_field_paths
    ])


def test_check_empty():
    empty_fields = {
        'field_string': '',
        'field_markdown': '',
        'field_int': None,
        'field_date': None,
        'field_enum': None,
        'field_user': None,
        'field_list': [],
        'field_object': {'nested1': ''},
        'field_list_objects': [{'nested1': ''}],
    }
    empty_field_paths = [
        'field_string', 'field_markdown', 'field_int', 'field_date', 'field_enum', 'field_user',
        'field_list', 'field_object.nested1', 'field_list_objects[0].nested1',
    ]
    project_type = create_project_type()
    set_all_required(project_type.report_fields, True)
    set_all_required(project_type.finding_fields, True)
    project_type.save()
    project = create_project(
        project_type=project_type,
        report_data=ensure_defined_structure(value=empty_fields, definition=project_type.report_fields_obj, handle_undefined=HandleUndefinedFieldsOptions.FILL_NONE),
    )
    finding = create_finding(
        project=project,
        data=ensure_defined_structure(value=empty_fields, definition=project_type.finding_fields_obj, handle_undefined=HandleUndefinedFieldsOptions.FILL_NONE),
    )

    assertContainsCheckResults(project.perform_checks(), [
        ErrorMessage(level=MessageLevel.WARNING, message='Empty field', location=MessageLocationInfo(
            type=MessageLocationType.SECTION, id='other', path=p))
        for p in empty_field_paths
    ] + [
        ErrorMessage(level=MessageLevel.WARNING, message='Empty field', location=MessageLocationInfo(
            type=MessageLocationType.FINDING, id=finding.finding_id, path=p))
        for p in empty_field_paths
    ])


def test_check_empty_not_required():
    empty_fields = {
        'field_string': '',
        'field_markdown': '',
        'field_int': None,
        'field_date': None,
        'field_enum': None,
        'field_user': None,
        'field_list': [],
        'field_object': {'nested1': ''},
        'field_list_objects': [{'nested1': ''}],
    }
    empty_field_paths = [
        'field_string', 'field_markdown', 'field_int', 'field_date', 'field_enum', 'field_user',
        'field_list', 'field_object.nested1', 'field_list_objects[0].nested1',
    ]
    project_type = create_project_type()
    set_all_required(project_type.report_fields, False)
    set_all_required(project_type.finding_fields, False)
    project_type.save()
    project = create_project(
        project_type=project_type,
        report_data=ensure_defined_structure(value=empty_fields, definition=project_type.report_fields_obj),
    )
    finding = create_finding(
        project=project,
        data=ensure_defined_structure(value=empty_fields, definition=project_type.finding_fields_obj),
    )

    assertNotContainsCheckResults(project.perform_checks(), [
        ErrorMessage(level=MessageLevel.WARNING, message='Empty field', location=MessageLocationInfo(
            type=MessageLocationType.SECTION, id='other', path=p))
        for p in empty_field_paths
    ] + [
        ErrorMessage(level=MessageLevel.WARNING, message='Empty field', location=MessageLocationInfo(
            type=MessageLocationType.FINDING, id=finding.finding_id, path=p))
        for p in empty_field_paths
    ])


def test_invalid_cvss():
    project = create_project()
    finding_valid1 = create_finding(
        project=project, data={'cvss': 'CVSS:3.0/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H'})
    finding_valid2 = create_finding(
        project=project, data={'cvss': 'AV:N/AC:L/Au:N/C:C/I:C/A:C'})
    finding_valid3 = create_finding(project=project, data={'cvss': 'n/a'})
    finding_invalid1 = create_finding(
        project=project, data={'cvss': 'CVSS:3.1/asdf'})
    finding_invalid2 = create_finding(
        project=project, data={'cvss': 'invalid CVSS'})

    assertContainsCheckResults(project.perform_checks(), [
        ErrorMessage(level=MessageLevel.WARNING, message='Invalid CVSS vector', location=MessageLocationInfo(
            type=MessageLocationType.FINDING, id=f.finding_id, path='cvss'))
        for f in [finding_invalid1, finding_invalid2]
    ])
    assertNotContainsCheckResults(project.perform_checks(), [
        ErrorMessage(level=MessageLevel.WARNING, message='Invalid CVSS vector', location=MessageLocationInfo(
            type=MessageLocationType.FINDING, id=f.finding_id, path='cvss'))
        for f in [finding_valid1, finding_valid2, finding_valid3]
    ])


@pytest.mark.parametrize(('expected', 'cvss_version', 'cvss_vector'), [
    (True, None, 'CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:H/SI:H/SA:H'),
    (True, None, 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H'),
    (True, None, 'CVSS:3.0/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H'),
    (True, None, 'AV:N/AC:L/Au:N/C:C/I:C/A:C'),
    (True, None, 'n/a'),
    (True, 'CVSS:4.0', 'CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:H/SI:H/SA:H'),
    (False, 'CVSS:4.0', 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H'),
    (True, 'CVSS:4.0', 'n/a'),
    (True, 'CVSS:3.1', 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H'),
    (False, 'CVSS:3.1', 'CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:H/SI:H/SA:H'),
])
def test_invalid_cvss_version(expected, cvss_version, cvss_vector):
    project = create_project(findings_kwargs=[], project_type=create_project_type(finding_fields={
        'title': {'type': 'string'},
        'cvss': {'type': 'cvss', 'cvss_version': cvss_version},
    }))
    finding = create_finding(project=project, data={'cvss': cvss_vector})

    check_res = project.perform_checks()
    msg = ErrorMessage(level=MessageLevel.WARNING, message='Invalid CVSS version', location=MessageLocationInfo(
        type=MessageLocationType.FINDING, id=finding.finding_id, path='cvss'))
    if expected:
        assertNotContainsCheckResults(check_res, [msg])
    else:
        assertContainsCheckResults(check_res, [msg])


def test_review_status():
    project = create_project()
    finding_valid = create_finding(
        project=project, status=ReviewStatus.FINISHED)
    finding_invalid1 = create_finding(
        project=project, status=ReviewStatus.IN_PROGRESS)
    finding_invalid2 = create_finding(
        project=project, status=ReviewStatus.READY_FOR_REVIEW)
    finding_invalid3 = create_finding(
        project=project, status=ReviewStatus.NEEDS_IMPROVEMENT)

    section_valid = project.sections.first()
    section_valid.status = ReviewStatus.FINISHED
    section_valid.save()
    section_invalid = project.sections.exclude(id=section_valid.id).first()
    section_invalid.status = ReviewStatus.IN_PROGRESS
    section_invalid.save()

    assertContainsCheckResults(project.perform_checks(), [
        ErrorMessage(level=MessageLevel.WARNING, message='Status is not "finished"',
                     location=MessageLocationInfo(type=MessageLocationType.FINDING, id=f.finding_id))
        for f in [finding_invalid1, finding_invalid2, finding_invalid3]
    ] + [
        ErrorMessage(level=MessageLevel.WARNING, message='Status is not "finished"',
                     location=MessageLocationInfo(type=MessageLocationType.SECTION, id=s.section_id))
        for s in [section_invalid]
    ])
    assertNotContainsCheckResults(project.perform_checks(), [
        ErrorMessage(level=MessageLevel.WARNING, message='Status is not "finished"', location=MessageLocationInfo(
            type=MessageLocationType.FINDING, id=finding_valid.finding_id)),
        ErrorMessage(level=MessageLevel.WARNING, message='Status is not "finished"', location=MessageLocationInfo(
            type=MessageLocationType.SECTION, id=section_valid.section_id)),
    ])


@pytest.mark.parametrize(('pattern', 'value', 'expected'), [
    (r'^[a-z]+$', 'abc', True),
    (r'^[a-z]+$', 'abc123', False),
    (r'^([a-$', 'abc', 'error'),
])
def test_regex_check(pattern, value, expected):
    p = create_project(project_type=create_project_type(finding_fields={
        'title': {'type': 'string'},
        'field_regex': {'type': 'string', 'pattern': pattern},
    }), findings_kwargs=[])
    f = create_finding(project=p, data={'field_regex': value})

    check_res = p.perform_checks()
    msg_invalid = ErrorMessage(level=MessageLevel.WARNING, message='Invalid format', location=MessageLocationInfo(
        type=MessageLocationType.FINDING, id=f.finding_id, path='field_regex'))
    msg_error = ErrorMessage(level=MessageLevel.ERROR, message='Invalid regex pattern', location=MessageLocationInfo(
        type=MessageLocationType.FINDING, id=f.finding_id, path='field_regex'))
    assertContainsCheckResults(check_res, ([msg_invalid] if expected is False else [
    ]) + ([msg_error] if expected == 'error' else []))
    assertNotContainsCheckResults(check_res, ([msg_invalid] if expected is not False else [
    ]) + ([msg_error] if expected != 'error' else []))


@override_settings(REGEX_VALIDATION_TIMEOUT=timedelta(milliseconds=0.000001))
def test_regex_timeout():
    p = create_project(project_type=create_project_type(finding_fields={
        'title': {'type': 'string'},
        'field_regex': {'type': 'string', 'pattern': r'^[a-z]+$'},
    }), findings_kwargs=[])
    f = create_finding(project=p, data={'field_regex': 'abc'})
    assertContainsCheckResults(p.perform_checks(), [
        ErrorMessage(level=MessageLevel.ERROR, message='Regex timeout', location=MessageLocationInfo(
            type=MessageLocationType.FINDING, id=f.finding_id, path='field_regex')),
    ])


def test_comments():
    user = create_user()
    project = create_project(members=[user], findings_kwargs=[])
    finding = create_finding(project=project)
    section = project.sections.get(section_id='other')
    comment_open1 = create_comment(finding=finding, path='data.field_markdown', status=CommentStatus.OPEN, user=user)
    comment_open2 = create_comment(section=section, path='data.field_enum', status=CommentStatus.OPEN, user=user)
    comment_resolved1 = create_comment(finding=finding, path='data.field_cvss', status=CommentStatus.RESOLVED, user=user)
    comment_resolved2 = create_comment(section=section, path='data.field_string', status=CommentStatus.RESOLVED, user=user)

    assertContainsCheckResults(project.perform_checks(), [
        ErrorMessage(level=MessageLevel.WARNING, message='Unresolved comment', location=MessageLocationInfo(
            type=MessageLocationType.FINDING, id=finding.finding_id, path=comment_open1.path.removeprefix('data.'))),
        ErrorMessage(level=MessageLevel.WARNING, message='Unresolved comment', location=MessageLocationInfo(
            type=MessageLocationType.SECTION, id=section.section_id, path=comment_open2.path.removeprefix('data.'))),
    ])
    assertNotContainsCheckResults(project.perform_checks(), [
        ErrorMessage(level=MessageLevel.WARNING, message='Unresolved comment', location=MessageLocationInfo(
            type=MessageLocationType.FINDING, id=finding.finding_id, path=comment_resolved1.path.removeprefix('data.'))),
        ErrorMessage(level=MessageLevel.WARNING, message='Unresolved comment', location=MessageLocationInfo(
            type=MessageLocationType.SECTION, id=section.section_id, path=comment_resolved2.path.removeprefix('data.'))),
    ])
