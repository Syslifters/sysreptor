import io
from typing import Iterator
from uuid import uuid4
from django.core.files import File
from reportcreator_api.archive.crypto import base as crypto


class EncryptedFileAdapter(File):
    def chunks(self, *args, **kwargs) -> Iterator[bytes]:
        buf = io.BytesIO()
        with crypto.open(fileobj=buf, mode='wb') as c:
            for b in self.file.chunks(*args, **kwargs):
                c.write(b)
                yield buf.getvalue()
                buf.truncate(0)
                buf.seek(0)
        yield buf.getvalue()


class EncryptedStorageMixin:
    def open(self, name, mode='rb', **kwargs):
        return File(file=crypto.open(fileobj=super().open(name=name, mode=mode, **kwargs), mode=mode), name=name)
    
    def save(self, name, content, max_length=None):
        return super().save(name=str(uuid4()), content=EncryptedFileAdapter(file=File(content)), max_length=max_length)
    
    def size(self, name):
        size = super().size(name)
        with crypto.open(fileobj=super().open(name=name, mode='rb'), mode='r') as c:
            if hasattr(c, 'header_len') and hasattr(c, 'auth_tag_len'):
                size -= c.header_len + c.auth_tag_len
        return size

    def get_available_filename(self, name, max_length=None):
        return super().get_available_filename(name=str(uuid4()), max_length=None)
    
    def get_alternative_name(self, *args, **kwargs):
        return str(uuid4())
   

