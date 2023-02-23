import os

from django.core.files.storage import FileSystemStorage
from storages.backends.s3boto3 import S3Boto3Storage

from reportcreator_api.archive.crypto.storage import EncryptedStorageMixin


class FileSystemOverwriteStorage(FileSystemStorage):
    """
    FileSystemStorage that overwrites the original file if it already exists
    """
    def __init__(self, location=None, base_url=None, file_permissions_mode=None, directory_permissions_mode=None, **kwargs):
        super().__init__(
            location=location, 
            base_url=base_url, 
            file_permissions_mode=file_permissions_mode, 
            directory_permissions_mode=directory_permissions_mode, 
            **kwargs
        )

        # Create directory if it does not exist
        if not os.path.exists(location):
            os.makedirs(location)

    def _save(self, name, content):
        self.delete(name)
        return super()._save(name, content)


class EncryptedFileSystemStorage(EncryptedStorageMixin, FileSystemStorage):
    def __init__(self, location=None, base_url=None, file_permissions_mode=None, directory_permissions_mode=None, **kwargs):
        super().__init__(
            location=location, 
            base_url=base_url, 
            file_permissions_mode=file_permissions_mode, 
            directory_permissions_mode=directory_permissions_mode, 
        )


class EncryptedS3Storage(EncryptedStorageMixin, S3Boto3Storage):
    def __init__(self, access_key=None, secret_key=None, bucket_name=None, endpoint_url=None, **kwargs) -> None:
        super().__init__(
            access_key=access_key, 
            secret_key=secret_key, 
            bucket_name=bucket_name, 
            endpoint_url=endpoint_url
        )

