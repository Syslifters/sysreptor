import io
from typing import Iterator
from uuid import uuid4
from django.core.files import File
from reportcreator_api.archive.crypto import base as crypto


class IterableToFileAdapter(File):
    def __init__(self, iterable, name=None) -> None:
        super().__init__(file=None, name=name)
        self.iterator = iter(iterable)
        self.buffer = b''

    def read(self, size=-1):
        while len(self.buffer) < size or size == -1:
            try:
                self.buffer += next(self.iterator)
            except StopIteration:
                break
        
        out = self.buffer[:size]
        self.buffer = self.buffer[size:]
        return out

    @property
    def closed(self) -> bool:
        return False

    def seekable(self) -> bool:
        return False


class EncryptedFileAdapter(File):
    def __init__(self, file, name=None, **kwargs) -> None:
        self._original_file = file
        self._crypto_kwargs = kwargs
        super().__init__(IterableToFileAdapter(self._encrypted_chunks(file), name or file.name))

    def _encrypted_chunks(self, file, chunk_size=None):
        buf = io.BytesIO()
        with crypto.open(fileobj=buf, mode='wb', **self._crypto_kwargs) as c:
            for b in file.chunks(chunk_size=chunk_size):
                c.write(b)
                yield buf.getvalue()
                buf.truncate(0)
                buf.seek(0)
        yield buf.getvalue()
    
    def chunks(self, chunk_size=None) -> Iterator[bytes]:
        return self._encrypted_chunks(self._original_file, chunk_size)


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

    def get_available_name(self, name, max_length=None):
        randname = str(uuid4())
        randname_with_dir = randname[:2] + '/' + randname[2:]
        return super().get_available_name(name=randname_with_dir, max_length=None)

