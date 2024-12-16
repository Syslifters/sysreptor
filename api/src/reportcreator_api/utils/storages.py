from pathlib import Path

from django.core.files.storage import FileSystemStorage, InMemoryStorage
from storages.backends.s3 import S3Storage

from reportcreator_api.utils.crypto.storage import EncryptedStorageMixin


class FileSystemOverwriteStorage(FileSystemStorage):
    """
    FileSystemStorage that overwrites the original file if it already exists
    """
    def __init__(self, location=None, **kwargs):
        super().__init__(location=location, **kwargs)

        # Create directory if it does not exist
        Path(location).mkdir(parents=True, exist_ok=True)

    def _save(self, name, content):
        self.delete(name)
        return super()._save(name, content)


class UnencryptedFileSystemStorage(FileSystemStorage):
    def __init__(self, location=None, base_url=None, file_permissions_mode=None, directory_permissions_mode=None, **kwargs):
        super().__init__(
            location=location,
            base_url=base_url,
            file_permissions_mode=file_permissions_mode,
            directory_permissions_mode=directory_permissions_mode,
        )


class EncryptedFileSystemStorage(EncryptedStorageMixin, UnencryptedFileSystemStorage):
    pass


class UnencryptedS3Storage(S3Storage):
    def __init__(self, access_key=None, secret_key=None, security_token=None, bucket_name=None, endpoint_url=None, location=None, **kwargs) -> None:
        super().__init__(
            access_key=access_key,
            secret_key=secret_key,
            security_token=security_token,
            bucket_name=bucket_name,
            endpoint_url=endpoint_url,
            location=str(location),
        )

    def get_default_settings(self):
        return super().get_default_settings() | {
            'security_token': None,
        }


class EncryptedS3Storage(EncryptedStorageMixin, UnencryptedS3Storage):
    pass


class EncryptedInMemoryStorage(EncryptedStorageMixin, InMemoryStorage):
    def __init__(self, **kwargs) -> None:
        super().__init__()

