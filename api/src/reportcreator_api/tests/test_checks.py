import pytest
from reportcreator_api.pentests.models import ReviewStatus
from reportcreator_api.tests.mock import create_finding, create_project, create_project_type
from reportcreator_api.utils.error_messages import MessageLevel, MessageLocationInfo, MessageLocationType, ErrorMessage


pytestmark = pytest.mark.django_db


def assertContainsCheckResults(actual, expected):
    for e in expected:
        for a in actual:
            if e.message == a.message and e.location.type == a.location.type and e.location.id == a.location.id and e.location.path == a.location.path:
                break
        else:
            assert False, f'{e} not in check results'


def assertNotContainsCheckResults(actual, expected):
    for e in expected:
        for a in actual:
            if e.message == a.message and e.location.type == a.location.type and e.location.id == a.location.id and e.location.path == a.location.path:
                assert False, f'{e} in check results'


def set_all_required(definiton, required):
    if definiton.get('type'):
        definiton['required'] = required
        if definiton['type'] == 'object':
            set_all_required(definiton['properties'], required)
        elif definiton['type'] == 'list':
            set_all_required(definiton['items'], required)
    elif isinstance(definiton, dict):
        for k, d in definiton.items():
            set_all_required(d, required)


def test_check_todo():
    todo_fields = {
        'field_string': 'TODO: content',
        'field_markdown': 'Multiline markdown \nwith ![image](To-do) in markdown\n\n* item1\n* TODO: more items',
        'field_list': ['item1', 'ToDo: more items'],
        'field_object': {'nested1': 'nested todo in object'},
        'field_list_objects': [{'nested1': 'TODO'}],
    }
    todo_field_paths = ['field_string', 'field_markdown', 'field_list[1]', 'field_object.nested1', 'field_list_objects[0].nested1']
    project = create_project(report_data=todo_fields)
    finding = create_finding(project=project, data=todo_fields)

    assertContainsCheckResults(project.perform_checks(), [
        ErrorMessage(level=MessageLevel.WARNING, message='Unresolved TODO', location=MessageLocationInfo(type=MessageLocationType.SECTION, id='other', path=p)) 
        for p in todo_field_paths
    ] + [
        ErrorMessage(level=MessageLevel.WARNING, message='Unresolved TODO', location=MessageLocationInfo(type=MessageLocationType.FINDING, id=finding.finding_id, path=p)) 
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
        'field_list', 'field_object.nested1', 'field_list_objects[0].nested1'
    ]
    project_type = create_project_type()
    set_all_required(project_type.report_fields, True)
    set_all_required(project_type.finding_fields, True)
    project_type.save()
    project = create_project(project_type=project_type, report_data=empty_fields)
    finding = create_finding(project=project, data=empty_fields)

    assertContainsCheckResults(project.perform_checks(), [
        ErrorMessage(level=MessageLevel.WARNING, message='Empty field', location=MessageLocationInfo(type=MessageLocationType.SECTION, id='other', path=p)) 
        for p in empty_field_paths
    ] + [
        ErrorMessage(level=MessageLevel.WARNING, message='Empty field', location=MessageLocationInfo(type=MessageLocationType.FINDING, id=finding.finding_id, path=p)) 
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
        'field_list', 'field_object.nested1', 'field_list_objects[0].nested1'
    ]
    project_type = create_project_type()
    set_all_required(project_type.report_fields, False)
    set_all_required(project_type.finding_fields, False)
    project_type.save()
    project = create_project(project_type=project_type, report_data=empty_fields)
    finding = create_finding(project=project, data=empty_fields)

    assertNotContainsCheckResults(project.perform_checks(), [
        ErrorMessage(level=MessageLevel.WARNING, message='Empty field', location=MessageLocationInfo(type=MessageLocationType.SECTION, id='other', path=p)) 
        for p in empty_field_paths
    ] + [
        ErrorMessage(level=MessageLevel.WARNING, message='Empty field', location=MessageLocationInfo(type=MessageLocationType.FINDING, id=finding.finding_id, path=p)) 
        for p in empty_field_paths
    ])


def test_invalid_cvss():
    project = create_project()
    finding_valid1 = create_finding(project=project, data={'cvss': 'CVSS:3.0/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H'})
    finding_valid2 = create_finding(project=project, data={'cvss': 'AV:N/AC:L/Au:N/C:C/I:C/A:C'})
    finding_valid3 = create_finding(project=project, data={'cvss': 'n/a'})
    finding_invalid1 = create_finding(project=project, data={'cvss': 'CVSS:3.1/asdf'})
    finding_invalid2 = create_finding(project=project, data={'cvss': 'invalid CVSS'})

    assertContainsCheckResults(project.perform_checks(), [
        ErrorMessage(level=MessageLevel.WARNING, message='Invalid CVSS vector', location=MessageLocationInfo(type=MessageLocationType.FINDING, id=f.finding_id, path='cvss'))
        for f in [finding_invalid1, finding_invalid2]
    ])
    assertNotContainsCheckResults(project.perform_checks(), [
        ErrorMessage(level=MessageLevel.WARNING, message='Invalid CVSS vector', location=MessageLocationInfo(type=MessageLocationType.FINDING, id=f.finding_id, path='cvss'))
        for f in [finding_valid1, finding_valid2, finding_valid3]
    ])


def test_review_status():
    project = create_project()
    finding_valid = create_finding(project=project, status=ReviewStatus.FINISHED)
    finding_invalid1 = create_finding(project=project, status=ReviewStatus.IN_PROGRESS)
    finding_invalid2 = create_finding(project=project, status=ReviewStatus.READY_FOR_REVIEW)
    finding_invalid3 = create_finding(project=project, status=ReviewStatus.NEEDS_IMPROVEMENT)

    section_valid = project.sections.first()
    section_valid.status = ReviewStatus.FINISHED
    section_valid.save()
    section_invalid = project.sections.exclude(id=section_valid.id).first()
    section_invalid.status = ReviewStatus.IN_PROGRESS
    section_invalid.save()

    assertContainsCheckResults(project.perform_checks(), [
        ErrorMessage(level=MessageLevel.WARNING, message='Status is not "finished"', location=MessageLocationInfo(type=MessageLocationType.FINDING, id=f.finding_id))
        for f in [finding_invalid1, finding_invalid2, finding_invalid3]
    ] + [
        ErrorMessage(level=MessageLevel.WARNING, message='Status is not "finished"', location=MessageLocationInfo(type=MessageLocationType.SECTION, id=s.section_id))
        for s in [section_invalid]
    ])
    assertNotContainsCheckResults(project.perform_checks(), [
        ErrorMessage(level=MessageLevel.WARNING, message='Status is not "finished"', location=MessageLocationInfo(type=MessageLocationType.FINDING, id=finding_valid.finding_id)),
        ErrorMessage(level=MessageLevel.WARNING, message='Status is not "finished"', location=MessageLocationInfo(type=MessageLocationType.SECTION, id=section_valid.section_id)),
    ])