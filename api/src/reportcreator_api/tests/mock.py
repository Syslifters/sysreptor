import random
from datetime import datetime, timedelta
from unittest import mock
from django.utils import timezone
from rest_framework.test import APIClient
from reportcreator_api.archive import crypto
from reportcreator_api.archive.import_export.serializers import RelatedUserDataExportImportSerializer

from reportcreator_api.pentests.customfields.utils import HandleUndefinedFieldsOptions, ensure_defined_structure
from reportcreator_api.pentests.models import FindingTemplate, NotebookPage, PentestFinding, PentestProject, ProjectType, UploadedAsset, UploadedImage, \
    ProjectMemberInfo, ProjectMemberRole, UploadedProjectFile, UploadedUserNotebookImage, Language, UserPublicKey
from reportcreator_api.pentests.customfields.predefined_fields import finding_field_order_default, finding_fields_default, report_fields_default, \
    report_sections_default
from reportcreator_api.pentests.models.archive import ArchivedProject, ArchivedProjectKeyPart, ArchivedProjectPublicKeyEncryptedKeyPart
from reportcreator_api.users.models import PentestUser, MFAMethod
from django.core.files.uploadedfile import SimpleUploadedFile


def create_png_file() -> bytes:
    # 1x1 pixel PNG file
    # Source: https://commons.wikimedia.org/wiki/File:1x1.png
    return b'\x89PNG\r\n\x1a\n\x00\x00\x00\r' + \
           b'IHDR\x00\x00\x00\x01\x00\x00\x00\x01\x01\x03\x00\x00\x00%\xdbV\xca\x00\x00\x00\x03' + \
           b'PLTE\x00\x00\x00\xa7z=\xda\x00\x00\x00\x01tRNS\x00@\xe6\xd8f\x00\x00\x00\n' + \
           b'IDAT\x08\xd7c`\x00\x00\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82'


def create_user(mfa=False, public_key=False, notes_kwargs=None, images_kwargs=None, **kwargs) -> PentestUser:
    username = f'user{random.randint(0, 100000)}'
    user = PentestUser.objects.create_user(**{
        'username': username,
        'password': None,
        'email': username + '@example.com',
        'first_name': 'Herbert',
        'last_name': 'Testinger',
    } | kwargs)
    if mfa:
        MFAMethod.objects.create_totp(user=user, is_primary=True)
        MFAMethod.objects.create_backup(user=user)
    if public_key:
        create_public_key(user=user)

    for note_kwargs in notes_kwargs if notes_kwargs is not None else [{}]:
        create_notebookpage(user=user, **note_kwargs)
    for idx, image_kwargs in enumerate(images_kwargs if images_kwargs is not None else [{}]):
        UploadedUserNotebookImage.objects.create(linked_object=user, **{
            'name': f'file{idx}.png', 
            'file': SimpleUploadedFile(name=f'file{idx}.png', content=create_png_file())
        } | image_kwargs)

    return user


def create_imported_member(roles=None, **kwargs):
    username = f'user{random.randint(0, 100000)}'
    return RelatedUserDataExportImportSerializer(instance=ProjectMemberInfo(
        user=PentestUser(**{
            'username': username,
            'email': f'{username}@example.com',
            'first_name': 'Imported',
            'last_name': 'User',
        } | kwargs), 
        roles=roles if roles is not None else ProjectMemberRole.default_roles)).data


def create_template(**kwargs) -> FindingTemplate:
    data = {
        'title': f'Finding Template #{random.randint(1, 100000)}',
        'description': 'Template Description',
        'recommendation': 'Template Recommendation',
        'undefined_field': 'test',
    } | kwargs.pop('data', {})
    template =  FindingTemplate.objects.create(**{
        'language': Language.ENGLISH,
        'tags': ['web', 'dev'],
    } | kwargs)
    template.update_data(data)
    template.save()
    return template


def create_project_type(**kwargs) -> ProjectType:
    additional_fields = {
        'field_string': {'type': 'string', 'label': 'String Field', 'default': 'test'},
        'field_markdown': {'type': 'markdown', 'label': 'Markdown Field', 'default': '# test\nmarkdown'},
        'field_cvss': {'type': 'cvss', 'label': 'CVSS Field', 'default': 'n/a'},
        'field_date': {'type': 'date', 'label': 'Date Field', 'default': '2022-01-01'},
        'field_int': {'type': 'number', 'label': 'Number Field', 'default': 10},
        'field_bool': {'type': 'boolean', 'label': 'Boolean Field', 'default': False},
        'field_enum': {'type': 'enum', 'label': 'Enum Field', 'choices': [{'value': 'enum1', 'label': 'Enum Value 1'}, {'value': 'enum2', 'label': 'Enum Value 2'}], 'default': 'enum2'},
        'field_combobox': {'type': 'combobox', 'label': 'Combobox Field', 'suggestions': ['value 1', 'value 2'], 'default': 'value1'},
        'field_user': {'type': 'user', 'label': 'User Field'},
        'field_object': {'type': 'object', 'label': 'Nested Object', 'properties': {'nested1':  {'type': 'string', 'label': 'Nested Field'}}},
        'field_list': {'type': 'list', 'label': 'List Field', 'items': {'type': 'string'}},
        'field_list_objects': {'type': 'list', 'label': 'List of nested objects', 'items': {'type': 'object', 'properties': {'nested1': {'type': 'string', 'label': 'Nested object field', 'default': None}}}},
    }
    project_type = ProjectType.objects.create(**{
        'name': f'Project Type #{random.randint(1, 100000)}',
        'language': Language.ENGLISH,
        'report_fields': report_fields_default() | additional_fields,
        'report_sections': report_sections_default(),
        'finding_fields': finding_fields_default() | additional_fields,
        'finding_field_order': finding_field_order_default(),
        'report_template': '''<section><h1>{{ report.title }}</h1></section><section v-for="finding in findings"><h2>{{ finding.title }}</h2></section>''',
        'report_styles': '''@page { size: A4 portrait; } h1 { font-size: 3em; font-weight: bold; }''',
        'report_preview_data': {
            'report': {'title': 'Demo Report', 'field_string': 'test', 'field_int': 5, 'undefined_field': 'test'}, 
            'findings': [{'title': 'Demo finding', 'undefined_field': 'test'}]
        }
    } | kwargs)
    UploadedAsset.objects.create(linked_object=project_type, name='file1.png', file=SimpleUploadedFile(name='file1.png', content=b'file1'))
    UploadedAsset.objects.create(linked_object=project_type, name='file2.png', file=SimpleUploadedFile(name='file2.png', content=b'file2'))
    return project_type


def create_finding(project, template=None, **kwargs) -> PentestFinding:
    data = ensure_defined_structure(
        value={
            'title': f'Finding #{random.randint(0, 100000)}',
            'cvss': 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H',
            'description': 'Finding Description',
            'recommendation': 'Finding Recommendation',
            'undefined_field': 'test',
        } | (template.data if template else {}),
        definition=project.project_type.finding_fields_obj,
        handle_undefined=HandleUndefinedFieldsOptions.FILL_DEFAULT,
        include_undefined=True,
    ) | kwargs.pop('data', {})
    finding = PentestFinding.objects.create(**{
        'project': project,
        'assignee': None,
        'template_id': template.id if template else None,
    } | kwargs)
    finding.update_data(data)
    finding.save()
    return finding


def create_notebookpage(**kwargs) -> NotebookPage:
    return NotebookPage.objects.create(**{
        'title': f'Note #{random.randint(0, 100000)}',
        'text': 'Note text',
        'checked': random.choice([None, True, False]),
        'icon_emoji': random.choice([None, '🦖']),
        'status_emoji': random.choice([None, '✔️', '🤡']),
    } | kwargs)


def create_project(project_type=None, members=[], report_data={}, findings_kwargs=None, notes_kwargs=None, images_kwargs=None, files_kwargs=None, **kwargs) -> PentestProject:
    project_type = project_type or create_project_type()
    project = PentestProject.objects.create(**{
        'project_type': project_type,
        'name': f'Pentest Project #{random.randint(1, 100000)}',
        'language': Language.ENGLISH,
        'tags': ['web', 'customer:test'],
    } | kwargs)
    project.update_data({
        'title': 'Report title',
        'undefined_field': 'test',
    } | report_data)
    project.save()

    member_infos = []
    for m in members:
        if isinstance(m, PentestUser):
            member_infos.append(ProjectMemberInfo(project=project, user=m, roles=[ProjectMemberRole.default_roles]))
        elif isinstance(m, ProjectMemberInfo):
            m.project = project
            member_infos.append(m)
        else:
            raise ValueError('Unsupported member type')
    ProjectMemberInfo.objects.bulk_create(member_infos)

    for finding_kwargs in findings_kwargs if findings_kwargs is not None else [{}] * 3:
        create_finding(project=project, **finding_kwargs)
    
    for note_kwargs in notes_kwargs if notes_kwargs is not None else [{}] * 3:
        create_notebookpage(project=project, **note_kwargs)

    for idx, image_kwargs in enumerate(images_kwargs if images_kwargs is not None else [{}] * 2):
        UploadedImage.objects.create(linked_object=project, **{
            'name': f'file{idx}.png', 
            'file': SimpleUploadedFile(name=f'file{idx}.png', content=create_png_file())
        } | image_kwargs)
    for idx, file_kwargs in enumerate(files_kwargs if files_kwargs is not None else [{}] * 2):
        UploadedProjectFile.objects.create(linked_object=project, **{
            'name': f'file{idx}.pdf', 
            'file': SimpleUploadedFile(name=f'file{idx}.pdf', content=f'%PDF-1.3{idx}'.encode())
        } | file_kwargs)

    return project


def create_public_key(**kwargs):
    dummy_data = {
        'name': f'Public key #{random.randint(1, 100000)}',
    }
    if 'public_key' not in kwargs:
        dummy_data |= {
            'public_key': 
                '-----BEGIN PGP PUBLIC KEY BLOCK-----\n\n' +
                'mDMEZBryexYJKwYBBAHaRw8BAQdAI2A6jJCXSGP10s2H1duX22saF2lX4CtGzX+H\n' +
                'xm4nN8W0LEF1dG9nZW5lcmF0ZWQgS2V5IDx1bnNwZWNpZmllZEA3MmNmMGYzYTc4\n' +
                'NmQ+iJAEExYIADgWIQTC5xEj3lvM80ruTt39spmRS6kHgwUCZBryewIbIwULCQgH\n' +
                'AgYVCgkICwIEFgIDAQIeAQIXgAAKCRD9spmRS6kHgxspAQDrxnxj2eRaubEX547n\n' +
                'w+wE1PJohJqLoWERuCz2UuJLRwEA44NZVlPHdkwUXeP7otuOeA0ZCzOQIc+/60Pr\n' +
                'aeqVEQi4cwRkGvJ7EgUrgQQAIgMDBHlYyMT98UVGIaFUu2p/rkbOGnZ1k5d/KtMx\n' +
                '8TxqyU1cpdIzTvOVD4ykunTzsWsi60ERcNg6vDuHcDCapHYmvuk/+g49NQFNutRX\n' +
                'fnNxVj091cH3ioJCgQ1wbYgoW0qfCQMBCQiIeAQYFggAIBYhBMLnESPeW8zzSu5O\n' +
                '3f2ymZFLqQeDBQJkGvJ7AhsMAAoJEP2ymZFLqQeDrOUBAKnrakgp/dYWsMIHwiAg\n' +
                'Nq1F1YAX92oNteAVpTRNkwyIAQC68j1ytjpdoEbYlAPfQtKljjDSDONLxmmZWPxP\n' +
                'Ya8sAg==\n' +
                '=jbm4\n' +
                '-----END PGP PUBLIC KEY BLOCK-----\n',
            'public_key_info': {
                'cap': 'scaESCA', 
                'algo': '22', 
                'type': 'pub', 
                'curve': 'ed25519', 
                'subkey_info': {
                    'C3B01D1054571D18': {
                        'cap': 'e', 
                        'algo': '18', 
                        'type': 'sub', 
                        'curve': 'nistp384', 
                    }
                }
            }
        }

    return UserPublicKey.objects.create(**dummy_data | kwargs)


def create_archived_project(project=None, **kwargs):
    name = project.name if project else f'Archive #{random.randint(1, 100000)}'
    users = [m.user for m in project.members.all()] if project else [create_user(public_key=True)]

    archive = ArchivedProject.objects.create(name=name, threshold=1, file=SimpleUploadedFile('archive.tar.gz', crypto.MAGIC + b'dummy-data'))
    key_parts = []
    encrypted_key_parts = []
    for u in users:
        key_parts.append(ArchivedProjectKeyPart(archived_project=archive, user=u, encrypted_key_part=b'dummy-data'))
        for pk in u.public_keys.all():
            encrypted_key_parts.append(ArchivedProjectPublicKeyEncryptedKeyPart(key_part=key_parts[-1], public_key=pk, encrypted_data='dummy-data'))
            
    if not encrypted_key_parts:
        raise ValueError('No public keys set for users')
    ArchivedProjectKeyPart.objects.bulk_create(key_parts)
    ArchivedProjectPublicKeyEncryptedKeyPart.objects.bulk_create(encrypted_key_parts)
    return archive


def mock_time(before=None, after=None):
    return mock.patch('django.utils.timezone.now',
                      lambda: datetime.now(tz=timezone.get_current_timezone()) - (before or timedelta()) + (after or timedelta()))


def api_client(user=None):
    client = APIClient()
    client.force_authenticate(user)
    return client

