import re
from datetime import timedelta
from unittest import mock
from uuid import uuid4

import pytest
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import storages
from django.core.management import call_command
from django.test import override_settings
from django.utils import timezone

from sysreptor.pentests import storages as pentest_storages
from sysreptor.pentests.models import UploadedAsset, UploadedImage
from sysreptor.tests.mock import create_project, create_project_type, mock_time, update


def file_exists(file) -> bool:
    try:
        with file.open():
            return True
    except (ValueError, FileNotFoundError):
        return False


@pytest.mark.parametrize(('original', 'cleaned'), [
    ('test.txt', 'test.txt'),
    # Attacks
    ('te\x00st.txt', 'te-st.txt'),
    ('te/st.txt', 'st.txt'),
    ('t/../../../est.txt', 'est.txt'),
    ('../test1.txt', 'test1.txt'),
    ('..', 'file'),
    # Markdown conflicts
    ('/test2.txt', 'test2.txt'),
    ('t**es**t.txt', 't--es--t.txt'),
    ('te_st_.txt', 'te-st-.txt'),
    ('t![e]()st.txt', 't--e---st.txt'),
])
@pytest.mark.django_db()
def test_uploadedfile_filename(original, cleaned):
    actual_name = UploadedAsset.objects.create(name=original, file=ContentFile(content=b'test', name='test'), linked_object=create_project_type()).name
    assert actual_name == cleaned


@pytest.mark.django_db()
@override_settings(UPLOAD_RANDOMIZE_NAME=True)
def test_upload_name_always_suffixed_except_design_assets():
    project = create_project(images_kwargs=[], files_kwargs=[])
    project_type = create_project_type(assets_kwargs=[])

    upload_suffix_pattern = re.compile(r'^.+-[A-Za-z0-9]{8}\.png$')

    img = UploadedImage.objects.create(
        name='test.png', file=ContentFile(content=b'test', name='test.png'), linked_object=project)
    assert img.name != 'test.png'
    assert upload_suffix_pattern.match(img.name)

    img2 = UploadedImage.objects.create(
        name='test.png', file=ContentFile(content=b'test2', name='test.png'), linked_object=project)
    assert img2.name != img.name
    assert upload_suffix_pattern.match(img2.name)

    asset = UploadedAsset.objects.create(
        name='test.png', file=ContentFile(content=b'test', name='test.png'), linked_object=project_type)
    assert asset.name == 'test.png'

    asset2 = UploadedAsset.objects.create(
        name='test.png', file=ContentFile(content=b'test2', name='test.png'), linked_object=project_type)
    assert asset2.name != 'test.png'
    assert upload_suffix_pattern.match(asset2.name)


@pytest.mark.django_db()
class TestFileDelete:
    @pytest.fixture(autouse=True)
    def setUp(self):
        with override_settings(SIMPLE_HISTORY_ENABLED=False):
            self.project = create_project()
            self.image = self.project.images.first()
            self.asset = self.project.project_type.assets.first()
            yield

    def test_delete_file_referenced_only_once(self):
        self.image.delete()
        assert not file_exists(self.image.file)

        self.asset.delete()
        assert not file_exists(self.asset.file)

    def test_delete_file_referenced_multiple_times(self):
        UploadedImage.objects.create(linked_object=self.image.linked_object, name='new.png', file=self.image.file)
        self.image.delete()
        assert file_exists(self.image.file)

        UploadedAsset.objects.create(linked_object=self.asset.linked_object, name='new.png', file=self.asset.file)
        self.asset.delete()
        assert file_exists(self.asset.file)

    def test_delete_copied_images(self):
        p = create_project()
        p2 = p.copy()

        images = list(p.images.order_by('name_hash'))
        for o, c in zip(images, p2.images.order_by('name_hash'), strict=False):
            assert o.file == c.file
        p.delete()
        for i in images:
            assert file_exists(i.file)

    def test_delete_copied_assets(self):
        t = create_project_type()
        t2 = t.copy()

        assets = list(t.assets.order_by('name_hash'))
        for o, c in zip(assets, t2.assets.order_by('name_hash'), strict=False):
            assert o.file == c.file
        t.delete()
        for a in assets:
            assert file_exists(a.file)

    def test_delete_cascade(self):
        pt = self.project.project_type
        pt.copy(linked_project=self.project)
        pt2 = pt.copy(linked_project=self.project)
        update(self.project, project_type=pt2)
        pt.delete()
        self.project.delete()

        assert not file_exists(self.image.file)
        assert not file_exists(self.asset.file)


@pytest.mark.django_db()
class TestCleanupFilesCommand:
    @pytest.fixture(autouse=True)
    def setUp(self):
        with (
            override_settings(STORAGES=settings.STORAGES | {
                'uploadedimages': {'BACKEND': 'django.core.files.storage.InMemoryStorage'},
            }),
            mock.patch.object(UploadedImage.file.field, 'storage', storages['uploadedimages']),
        ):
            yield

    def test_cleanup_database(self):
        p = create_project(images_kwargs=[{'name': 'image1.png'}, {'name': 'image2.png'}])
        image = p.images.filter_name('image1.png').get()
        image_history = image.history.first()

        # Simulate missing file on filesystem while DB still references it.
        storage = image.file.storage
        storage.delete(image.file.name)
        assert not file_exists(image.file)

        with mock_time(after=timedelta(days=10)):
            call_command('cleanupfiles', database=True, filesystem=False, storage='uploadedimages', verbosity=0)

        # Unreferenced images should be deleted
        assert not UploadedImage.objects.filter(pk=image.pk).exists()
        image_history.refresh_from_db()
        assert image_history.file == image.file.name

        # Referenced images should not be deleted
        image2 = p.images.filter_name('image2.png').get()
        assert file_exists(image2.file)

    def test_cleanup_filesystem_deletes_unreferenced_files(self):
        p = create_project(images_kwargs=[{'name': 'image.png'}])

        # Simulate orphan file on filesystem that is not referenced in the DB
        storage = pentest_storages.get_uploaded_image_storage()
        filename = f'orphan_{uuid4()}.png'
        orphan_name = storage.save(filename, ContentFile(content=b'orphan', name=filename))
        storage._resolve(orphan_name).created_time = timezone.now() - timedelta(days=10)
        assert storage.exists(orphan_name)

        with mock_time(after=timedelta(days=10)):
            call_command('cleanupfiles', database=False, filesystem=True, storage='uploadedimages', verbosity=0)

        # Orphan file should be deleted
        assert not storage.exists(orphan_name), f'{orphan_name=}, {storage=}, {UploadedImage.file.field.storage=}'

        # Referenced files should not be deleted
        image = p.images.first()
        assert file_exists(image.file)

    def test_cleanup_filesystem_history(self):
        p = create_project()
        image = p.images.first()
        image_history = image.history.first()
        f = image.file
        image.delete()

        with mock_time(after=timedelta(days=10)):
            call_command('cleanupfiles', database=False, filesystem=True, verbosity=0)

        # File should not be deleted because it is referenced in the history
        assert file_exists(f)
        assert not UploadedImage.objects.filter(pk=image.pk).exists()
        assert UploadedImage.history.filter(pk=image_history.pk).exists()
        image_history.refresh_from_db()
        assert image_history.file == f.name

