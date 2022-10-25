import io
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from reportcreator_api.pentests.models import PentestProject, ProjectType, SourceEnum, UploadedAsset, UploadedImage
from reportcreator_api.tests.utils import TestHelperMixin
from reportcreator_api.archive.import_export import export_project_types, export_projects, export_templates, import_project_types, import_projects, import_templates
from reportcreator_api.tests.mock import create_project, create_project_type, create_template, create_user


def archive_to_file(archive_iterator):
    return io.BytesIO(b''.join(archive_iterator))


class ImportExportTests(TestHelperMixin, TestCase):
    def setUp(self) -> None:
        self.user = create_user()
        self.template = create_template()
        self.project_type = create_project_type()
        self.project = create_project(
            project_type=self.project_type, 
            pentesters=[self.user],
            report_data={'field_user': str(self.user.id)},  
            findings_kwargs=[
                {'assignee': self.user, 'template': self.template},
                {'assignee': None, 'template': None},
            ])
    
    def test_export_import_template(self):
        archive = archive_to_file(export_templates([self.template]))
        imported = import_templates(archive)

        self.assertEqual(len(imported), 1)
        t = imported[0]

        self.assertKeysEqual(t, self.template, ['created', 'language', 'data', 'data_all'])
        self.assertEqual(set(t.tags), set(self.template.tags))
        self.assertEqual(t.source, SourceEnum.IMPORTED)

    def test_export_import_project_type(self):
        archive = archive_to_file(export_project_types([self.project_type]))
        imported = import_project_types(archive)

        self.assertEqual(len(imported), 1)
        t = imported[0]

        self.assertKeysEqual(t, self.project_type, [
            'created', 'name', 'language', 
            'report_fields', 'report_sections', 'finding_fields', 'finding_field_order', 
            'report_template', 'report_styles', 'report_preview_data'])
        self.assertEqual(t.source, SourceEnum.IMPORTED)
        
        self.assertSetEqual(
            {(a.name, a.file.read()) for a in t.assets.all()}, 
            {(a.name, a.file.read()) for a in self.project_type.assets.all()}
        )

    def test_export_import_project(self):
        archive = archive_to_file(export_projects([self.project]))
        imported = import_projects(archive)

        self.assertEqual(len(imported), 1)
        p = imported[0]

        self.assertKeysEqual(p, self.project, ['name', 'language'])
        self.assertSetEqual(set(p.pentesters.all()), set(self.project.pentesters.all()))
        self.assertEqual(p.data, self.project.data)
        self.assertEqual(p.data_all, self.project.data_all)
        self.assertEqual(p.source, SourceEnum.IMPORTED)
        
        self.assertEqual(p.sections.count(), self.project.sections.count())
        for i, s in zip(p.sections.order_by('section_id'), self.project.sections.order_by('section_id')):
            self.assertKeysEqual(i, s, ['section_id', 'created', 'assignee', 'data'])

        self.assertEqual(p.findings.count(), self.project.findings.count())
        for i, s in zip(p.findings.order_by('finding_id'), self.project.findings.order_by('finding_id')):
            self.assertKeysEqual(i, s, ['finding_id', 'created', 'assignee', 'template', 'data', 'data_all', 'risk_score', 'risk_level'])

        self.assertSetEqual(
            {(i.name, i.file.read()) for i in p.images.all()}, 
            {(i.name, i.file.read()) for i in self.project.images.all()}
        )

        self.assertKeysEqual(p.project_type, self.project.project_type, [
            'created', 'name', 'language', 
            'report_fields', 'report_sections', 'finding_fields', 'finding_field_order', 
            'report_template', 'report_styles', 'report_preview_data'])
        self.assertEqual(p.project_type.source, SourceEnum.IMPORTED_DEPENDENCY)
        self.assertEqual(p.project_type.linked_project, p)
        
        self.assertSetEqual(
            {(a.name, a.file.read()) for a in p.project_type.assets.all()}, 
            {(a.name, a.file.read()) for a in self.project.project_type.assets.all()}
        )

    def test_import_nonexistent_user(self):
        # export project with members and assignee, delete user, import => members and assignee == NULL
        # export project with UserField, delete user, import => user inlined in project.imported_pentesters
        archive = archive_to_file(export_projects([self.project]))
        old_user_id = self.user.id
        self.user.delete()
        p = import_projects(archive)[0]

        self.assertEqual(p.pentesters.count(), 0)
        self.assertEqual(p.sections.exclude(assignee=None).count(), 0)
        self.assertEqual(p.findings.exclude(assignee=None).count() , 0)

        # Check UUID of nonexistent user is still present in data
        self.assertEqual(p.data, self.project.data)
        for i, s in zip(p.findings.order_by('created'), self.project.findings.order_by('created')):
            self.assertKeysEqual(i, s, ['finding_id', 'created', 'assignee', 'template', 'data', 'data_all', 'risk_score', 'risk_level'])
        
        # Test nonexistent user is added to project.imported_pentesters
        self.assertEqual(len(p.imported_pentesters), 1)
        self.assertEqual(p.imported_pentesters[0]['id'], str(old_user_id))
        self.assertKeysEqual(p.imported_pentesters[0], self.user, [
            'email', 'phone', 'mobile',
            'name', 'title_before', 'first_name', 'middle_name', 'last_name', 'title_after',
        ])
    
    def test_import_nonexistent_template_reference(self):
        archive = archive_to_file(export_projects([self.project]))
        self.template.delete()
        p = import_projects(archive)[0]

        self.assertEqual(p.findings.exclude(template=None).count(), 0)

    def test_import_wrong_archive(self):
        archive = archive_to_file(export_templates([self.template]))
        with self.assertRaises(ValidationError):
            import_projects(archive)


class LinkedProjectTests(TestCase):
    def setUp(self) -> None:
        self.project_type = create_project_type(source=SourceEnum.IMPORTED_DEPENDENCY)
        self.project = create_project(project_type=self.project_type, source=SourceEnum.IMPORTED)
        self.project_type.linked_project = self.project
        self.project_type.save()
    
    def test_delete_linked_project(self):
        # On delete linked_project: project_type should also be deleted
        self.project.delete()
        self.assertEqual(ProjectType.objects.filter(id=self.project_type.id).exists(), False)
    
    def test_delete_linked_project_multiple_project_types(self):
        # On delete linked_project
        unused_pt = create_project_type(linked_project=self.project, source=SourceEnum.IMPORTED_DEPENDENCY)

        self.project.delete()
        self.assertEqual(ProjectType.objects.filter(id=self.project_type.id).exists(), False)
        self.assertEqual(ProjectType.objects.filter(id=unused_pt.id).exists(), False)
    
    def test_delete_linked_project_project_type_used_by_another_project(self):
        second_p = create_project(project_type=self.project_type)

        self.project.delete()
        self.assertEqual(ProjectType.objects.filter(id=self.project_type.id).exists(), True)
        self.assertEqual(PentestProject.objects.filter(id=second_p.id).exists(), True)
        self.project_type.refresh_from_db()
        self.assertEqual(self.project_type.linked_project, None)
    

class FileDeleteTests(TestCase):
    def setUp(self) -> None:
        p = create_project()
        self.image = p.images.first()
        self.asset = p.project_type.assets.first()

    def assertFileExists(self, file, expected):
        exists = False
        try:
            with file.open():
                exists = True
        except ValueError:
            exists = False
        self.assertEqual(exists, expected)
    
    def test_delete_file_referenced_only_once(self):
        self.image.delete()
        self.assertFileExists(self.image.file, False)

        self.asset.delete()
        self.assertFileExists(self.asset.file, False)

    def test_delete_file_referenced_multiple_times(self):
        UploadedImage.objects.create(linked_object=self.image.linked_object, name='new.png', file=self.image.file)
        self.image.delete()
        self.assertFileExists(self.image.file, True)

        UploadedAsset.objects.create(linked_object=self.asset.linked_object, name='new.png', file=self.asset.file)
        self.asset.delete()
        self.assertFileExists(self.asset.file, True)

    def test_delete_copied_images(self):
        p = create_project()
        p2 = p.copy()

        images = list(p.images.order_by('name'))
        for o, c in zip(images, p2.images.order_by('name')):
            self.assertEqual(o.file, c.file)
        p.delete()
        for i in images:
            self.assertFileExists(i.file, True)

    def test_delete_copied_assets(self):
        t = create_project_type()
        t2 = t.copy()

        assets = list(t.assets.order_by('name'))
        for o, c in zip(assets, t2.assets.order_by('name')):
            self.assertEqual(o.file, c.file)
        t.delete()
        for a in assets:
            self.assertFileExists(a.file, True)
