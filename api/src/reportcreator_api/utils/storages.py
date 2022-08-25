import os

from django.core.files.storage import FileSystemStorage


class FileSystemOverwriteStorage(FileSystemStorage):
    """
    FileSystemStorage that overwrites the original file if it already exists
    """
    def __init__(self, location, **kwargs):
        super().__init__(location=location, **kwargs)

        # Create directory if it does not exist
        if not os.path.exists(location):
            os.makedirs(location)

    def _save(self, name, content):
        self.delete(name)
        return super()._save(name, content)
