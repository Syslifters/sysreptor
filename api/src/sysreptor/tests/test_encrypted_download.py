import base64
import gzip
import json
import math
import tracemalloc

import pytest
from Cryptodome.Cipher import AES
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from sysreptor.pentests.models import UploadedImage, UploadedProjectFile
from sysreptor.tests.mock import (
    api_client,
    create_png_file,
    create_project,
    create_projectnotebookpage,
    create_shareinfo,
    create_user,
)
from sysreptor.utils.encrypted_download import (
    CHUNK_SIZE,
    FORMAT_VERSION,
    KEY_SIZE,
    NONCE_SIZE,
    encrypted_stream,
    gzip_stream,
)

ENCRYPTION_KEY = b'\x01' * KEY_SIZE
ENCRYPTION_KEY_HEADER_KWARGS = {'HTTP_X_SYSREPTOR_ENCRYPTION_KEY': base64.b64encode(ENCRYPTION_KEY).decode()}


def decrypt_frame(frame: bytes, index: int, final: bool = False, key: bytes = ENCRYPTION_KEY) -> bytes:
    data = base64.b64decode(frame)
    cipher = AES.new(key=key, mode=AES.MODE_GCM, nonce=data[:NONCE_SIZE])
    cipher.update(f'{FORMAT_VERSION}:{index}:{"final" if final else "data"}'.encode())
    return cipher.decrypt_and_verify(data[NONCE_SIZE:-16], data[-16:])


def read_frames(res) -> list[bytes]:
    return b''.join(res.streaming_content).split(b'\n')


def decrypt_frames(frames: list[bytes], key: bytes = ENCRYPTION_KEY) -> tuple[dict, bytes]:
    """
    Decrypt an encrypted download the same way the frontend does.
    """
    assert len(frames) >= 2

    metadata = json.loads(decrypt_frame(frames[0], index=0, key=key))
    content = b''.join(decrypt_frame(f, index=i + 1, key=key) for i, f in enumerate(frames[1:-1]))
    assert decrypt_frame(frames[-1], index=len(frames) - 1, final=True, key=key) == b''
    return metadata, content


def decrypt_response(res, key: bytes = ENCRYPTION_KEY) -> tuple[dict, bytes]:
    return decrypt_frames(read_frames(res), key=key)


class GeneratedFile:
    """File-like object of arbitrary size that generates its content on the fly."""

    def __init__(self, size: int):
        self.size = size
        self.position = 0
        self.closed = False

    def read(self, size: int = -1) -> bytes:
        remaining = self.size - self.position
        read_size = remaining if size is None or size < 0 else min(size, remaining)
        self.position += read_size
        return bytes(read_size)

    def close(self):
        self.closed = True


class TestEncryptedStreaming:
    """Large files are encrypted chunk by chunk and are never held in memory as a whole."""

    METADATA = {'version': FORMAT_VERSION, 'cipher': 'AES-GCM', 'filename': 'large.bin', 'content_type': 'application/octet-stream'}

    def test_file_is_read_lazily(self):
        file = GeneratedFile(size=100 * CHUNK_SIZE)
        stream = encrypted_stream(file=file, key=ENCRYPTION_KEY, metadata=self.METADATA)

        next(stream)
        assert file.position == 0
        next(stream)
        assert file.position == CHUNK_SIZE
        next(stream)
        assert file.position == 2 * CHUNK_SIZE

    def test_gzip_is_streamed_lazily(self):
        file = GeneratedFile(size=100 * CHUNK_SIZE)
        stream = gzip_stream(encrypted_stream(file=file, key=ENCRYPTION_KEY, metadata=self.METADATA))

        next(stream)
        assert file.position <= CHUNK_SIZE

    def measure_memory_usage(self, stream) -> tuple[int, int]:
        tracemalloc.start()
        try:
            blocks = sum(1 for _ in stream)
            _current, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        return blocks, peak

    def test_large_file_memory_usage(self):
        size = 1024 ** 3 + 1234
        file = GeneratedFile(size=size)

        frames, peak = self.measure_memory_usage(
            encrypted_stream(file=file, key=ENCRYPTION_KEY, metadata=self.METADATA))

        # metadata frame + content frames + final frame
        assert frames == math.ceil(size / CHUNK_SIZE) + 2
        assert file.position == size
        assert file.closed
        # Only single chunks are held in memory, not the whole file
        assert peak < 16 * 1024 * 1024, f'peak memory usage of {peak} bytes is too high'

    def test_large_file_memory_usage_gzip(self):
        # Smaller than the uncompressed case: compressing a GiB is slow and adds nothing to the assertion
        size = 128 * 1024 * 1024 + 1234
        file = GeneratedFile(size=size)

        _blocks, peak = self.measure_memory_usage(gzip_stream(
            encrypted_stream(file=file, key=ENCRYPTION_KEY, metadata=self.METADATA)))

        assert file.position == size
        assert file.closed
        assert peak < 16 * 1024 * 1024, f'peak memory usage of {peak} bytes is too high'


@pytest.mark.django_db()
class TestEncryptedFileDownload:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = create_user()
        self.project = create_project(members=[self.user])
        self.client = api_client(self.user)

    def create_file(self, name='file.pdf', content=b'file content'):
        return UploadedProjectFile.objects.create(
            linked_object=self.project, name=name, file=SimpleUploadedFile(name=name, content=content))

    def download(self, file, **kwargs):
        return self.client.get(
            reverse('uploadedprojectfile-retrieve-by-name', kwargs={'project_pk': self.project.pk, 'filename': file.name}),
            **kwargs)

    def test_download_without_header_unchanged(self):
        file = self.create_file()
        res = self.download(file)
        assert res.status_code == 200
        assert res.headers['Content-Type'] == 'application/octet-stream'
        assert res.headers['Content-Disposition'] == f'attachment; filename="{file.name}"'
        # Unencrypted downloads stay cacheable
        assert 'max-age=86400' in res.headers['Cache-Control']
        assert b''.join(res.streaming_content) == b'file content'

    def test_download_encrypted(self):
        file = self.create_file()
        res = self.download(file, **ENCRYPTION_KEY_HEADER_KWARGS)
        assert res.status_code == 200
        # Content type, filename and content are hidden from proxies
        assert res.headers['Content-Type'] == 'text/plain; charset=utf-8'
        assert res.headers['Content-Disposition'] == 'attachment'
        # Encrypted responses must not be cached: the ciphertext is only valid for the key of this request
        assert res.headers['Cache-Control'] == 'no-store'
        assert res.headers['X-Sysreptor-Id'] == str(file.id)

        metadata, content = decrypt_response(res)
        assert metadata == {
            'version': FORMAT_VERSION,
            'cipher': 'AES-GCM',
            'filename': file.name,
            'content_type': 'application/octet-stream',
        }
        assert content == b'file content'

    def test_download_encrypted_gzip(self):
        """base64 compresses well, therefore most of the base64 overhead is removed on the wire."""
        content = b'0123456789' * (CHUNK_SIZE // 5)
        file = self.create_file(content=content)

        res = self.download(file, **ENCRYPTION_KEY_HEADER_KWARGS, HTTP_ACCEPT_ENCODING='gzip')
        assert res.status_code == 200
        assert res.headers['Content-Encoding'] == 'gzip'
        assert 'Accept-Encoding' in res.headers['Vary']
        assert res.headers['Content-Type'] == 'text/plain; charset=utf-8'

        compressed = b''.join(res.streaming_content)
        decompressed = gzip.decompress(compressed)
        assert len(compressed) < len(decompressed)
        assert decrypt_frames(decompressed.split(b'\n'))[1] == content

    @pytest.mark.parametrize('accept_encoding', ['identity', ''])
    def test_download_encrypted_without_gzip(self, accept_encoding):
        file = self.create_file()
        res = self.download(file, **ENCRYPTION_KEY_HEADER_KWARGS, HTTP_ACCEPT_ENCODING=accept_encoding)
        assert 'Content-Encoding' not in res.headers
        assert decrypt_response(res)[1] == b'file content'

    def test_download_encrypted_does_not_leak_plaintext(self):
        file = self.create_file(name='secret-report.pdf', content=b'%PDF-1.3 secret content')
        body = b'\n'.join(read_frames(self.download(file, **ENCRYPTION_KEY_HEADER_KWARGS)))
        assert b'secret content' not in body
        assert b'secret-report.pdf' not in body
        assert b'%PDF' not in body

    def test_download_encrypted_multiple_chunks(self):
        content = b'0123456789' * (CHUNK_SIZE // 5)
        file = self.create_file(content=content)
        frames = read_frames(self.download(file, **ENCRYPTION_KEY_HEADER_KWARGS))

        # metadata frame + 2 content frames + final frame
        assert len(frames) == 4
        assert decrypt_frames(frames)[1] == content

    def test_download_encrypted_empty_file(self):
        file = self.create_file(content=b'')
        metadata, content = decrypt_response(self.download(file, **ENCRYPTION_KEY_HEADER_KWARGS))
        assert content == b''
        assert metadata['filename'] == file.name

    def test_download_encrypted_image(self):
        image = UploadedImage.objects.create(
            linked_object=self.project, name='image.png', file=SimpleUploadedFile(name='image.png', content=create_png_file()))
        res = self.client.get(reverse('uploadedimage-retrieve-by-name', kwargs={'project_pk': self.project.pk, 'filename': image.name}), **ENCRYPTION_KEY_HEADER_KWARGS)
        assert res.status_code == 200

        metadata, content = decrypt_response(res)
        assert metadata['content_type'] == 'image/png'
        assert metadata['filename'] == 'image.png'
        assert content == image.file.open().read()

    def test_frames_bound_to_index(self):
        """Frames cannot be reordered or dropped, because the frame index is authenticated."""
        file = self.create_file(content=b'0123456789' * (CHUNK_SIZE // 5))
        frames = read_frames(self.download(file, **ENCRYPTION_KEY_HEADER_KWARGS))

        with pytest.raises(ValueError, match='MAC check failed'):
            decrypt_frame(frames[2], index=1)
        with pytest.raises(ValueError, match='MAC check failed'):
            decrypt_frame(frames[-1], index=len(frames) - 1, final=False)

    def test_wrong_key(self):
        file = self.create_file()
        res = self.download(file, **ENCRYPTION_KEY_HEADER_KWARGS)
        with pytest.raises(ValueError, match='MAC check failed'):
            decrypt_response(res, key=b'\x02' * KEY_SIZE)

    @pytest.mark.parametrize('header_value', [
        'not-base64!',
        base64.b64encode(b'too-short').decode(),
        base64.b64encode(b'\x00' * 64).decode(),
        base64.b64encode(b'').decode() + 'x',
    ])
    def test_invalid_key(self, header_value):
        file = self.create_file()
        res = self.download(file, HTTP_X_SYSREPTOR_ENCRYPTION_KEY=header_value)
        assert res.status_code == 400


@pytest.mark.django_db()
class TestEncryptedFileDownloadEndpoints:
    """Encrypted downloads are available for all file download endpoints and enforce the same permissions."""

    def test_usernote_file(self):
        user = create_user(files_kwargs=[{
            'name': 'file.pdf',
            'file': SimpleUploadedFile(name='file.pdf', content=b'user file'),
        }])
        res = api_client(user).get(
            reverse('uploadedusernotebookfile-retrieve-by-name', kwargs={'pentestuser_pk': 'self', 'filename': 'file.pdf'}),
            **ENCRYPTION_KEY_HEADER_KWARGS)
        assert res.status_code == 200
        assert decrypt_response(res)[1] == b'user file'

    def test_shared_note_file(self):
        project = create_project(files_kwargs=[{'name': 'file.pdf', 'content': b'shared file'}])
        note = create_projectnotebookpage(project=project, text='[file](/files/name/file.pdf)')
        share_info = create_shareinfo(projectnote=note)

        res = api_client().get(
            reverse('sharednote-file-by-name', kwargs={'shareinfo_pk': share_info.id, 'filename': 'file.pdf'}),
            **ENCRYPTION_KEY_HEADER_KWARGS)
        assert res.status_code == 200
        assert decrypt_response(res)[1] == b'shared file'

    def test_shared_note_file_not_referenced(self):
        """Permission checks are applied before encrypting."""
        project = create_project(files_kwargs=[{'name': 'file.pdf', 'content': b'shared file'}])
        note = create_projectnotebookpage(project=project, text='no file reference')
        share_info = create_shareinfo(projectnote=note)

        res = api_client().get(
            reverse('sharednote-file-by-name', kwargs={'shareinfo_pk': share_info.id, 'filename': 'file.pdf'}),
            **ENCRYPTION_KEY_HEADER_KWARGS)
        assert res.status_code == 404

    def test_historic_file(self):
        user = create_user()
        project = create_project(members=[user], files_kwargs=[{'name': 'file.pdf', 'content': b'historic file'}])
        history_date = UploadedProjectFile.objects.get(name='file.pdf').history.first().history_date

        res = api_client(user).get(
            reverse('pentestprojecthistory-file-by-name', kwargs={
                'project_pk': project.pk, 'history_date': history_date.isoformat(), 'filename': 'file.pdf'}),
            **ENCRYPTION_KEY_HEADER_KWARGS)
        assert res.status_code == 200
        assert decrypt_response(res)[1] == b'historic file'

    def test_file_of_other_project(self):
        project = create_project(files_kwargs=[{'name': 'file.pdf'}])
        res = api_client(create_user()).get(
            reverse('uploadedprojectfile-retrieve-by-name', kwargs={'project_pk': project.pk, 'filename': 'file.pdf'}),
            **ENCRYPTION_KEY_HEADER_KWARGS)
        assert res.status_code == 404
