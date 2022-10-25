

from django.test import TestCase

from reportcreator_api.pentests.models import PentestProject
from .mock import create_project_type, create_project

class ModelDiffTests(TestCase):
    def setUp(self) -> None:
        self.project_type = create_project_type()
        self.project_type2 = create_project_type()
        self.project = create_project(project_type=self.project_type)
    
    def test_diff(self):
        p = PentestProject.objects.get(id=self.project.id)
        p.name = 'changed'
        p.update_data({'title': 'changed'})

        self.assertEqual(p.has_changed, True)
        self.assertSetEqual(set(p.changed_fields), {'name', 'custom_fields'})
        self.assertEqual(p.get_field_diff('name'), (self.project.name, p.name))
        self.assertEqual(p.get_field_diff('custom_fields'), (self.project.custom_fields, p.custom_fields))
    
    def test_diff_related(self):
        p = PentestProject.objects.get(id=self.project.id)
        p.project_type = self.project_type2
        self.assertEqual(p.has_changed, True)
        self.assertSetEqual(set(p.changed_fields), {'project_type_id'})
        self.assertEqual(p.get_field_diff('project_type_id'), (self.project_type.id, self.project_type2.id))

    def test_diff_deferred_fields(self):
        # Deferred fields should not cause DB queries
        with self.assertNumQueries(1):
            p = PentestProject.objects.only('id', 'readonly').get(id=self.project.id)
            
            # Changes on deferred fields are not detected
            p.name = 'changed'   # write deferred
            self.assertEqual(p.has_changed, False)

            # Changes on non-deferred fields are detected
            p.readonly = True
            self.assertEqual(p.has_changed, True)
