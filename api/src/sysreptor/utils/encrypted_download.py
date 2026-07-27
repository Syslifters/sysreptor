import base64
import json
from functools import wraps

from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
from django.utils.cache import patch_cache_control
from rest_framework import exceptions

from sysreptor.utils.api import StreamingHttpResponseAsync

# Header used by clients to opt in to encrypted downloads.
# The client generates the key, therefore responses recorded by a proxy cannot be decrypted by anyone else.
ENCRYPTION_KEY_HEADER = 'X-Sysreptor-Encryption-Key'

# Format version of the encrypted stream. Bumped on incompatible changes.
FORMAT_VERSION = 1

KEY_SIZE = 32
NONCE_SIZE = 12
CHUNK_SIZE = 512 * 1024


def get_encryption_key(request) -> bytes|None:
    """
    Get the client-provided encryption key from the request headers.
    Returns None if the client did not request an encrypted download.
    """
    header_value = request.headers.get(ENCRYPTION_KEY_HEADER)
    if not header_value:
        return None

    try:
        key = base64.b64decode(header_value, validate=True)
    except Exception:
        raise exceptions.ValidationError(f'Invalid {ENCRYPTION_KEY_HEADER} header: not valid base64') from None
    if len(key) != KEY_SIZE:
        raise exceptions.ValidationError(f'Invalid {ENCRYPTION_KEY_HEADER} header: expected a {KEY_SIZE} byte key')
    return key


def encrypt_frame(key: bytes, index: int, data: bytes, final: bool = False) -> bytes:
    """
    Encrypt a single frame of the stream as base64(nonce || ciphertext || tag).
    The frame index is authenticated, such that frames cannot be reordered, duplicated or dropped unnoticed.
    """
    cipher = AES.new(key=key, mode=AES.MODE_GCM, nonce=get_random_bytes(NONCE_SIZE))
    cipher.update(f'{FORMAT_VERSION}:{index}:{"final" if final else "data"}'.encode())
    ciphertext, tag = cipher.encrypt_and_digest(data)
    return base64.b64encode(cipher.nonce + ciphertext + tag)


def encrypted_stream(file, key: bytes, metadata: dict):
    """
    Encrypt a file as a stream of newline-separated base64 frames.

    The first frame contains the metadata (filename, content type), such that a proxy cannot
    derive anything about the file from the response. The last frame is empty and marks the end
    of the stream, such that truncated responses are detected instead of silently returning a partial file.
    """
    index = 0
    yield encrypt_frame(key=key, index=index, data=json.dumps(metadata).encode())

    try:
        while chunk := file.read(CHUNK_SIZE):
            index += 1
            yield b'\n' + encrypt_frame(key=key, index=index, data=chunk)
    finally:
        file.close()

    yield b'\n' + encrypt_frame(key=key, index=index + 1, data=b'', final=True)


def encrypted_file_response(file, key: bytes, filename: str, content_type: str, headers: dict|None = None):
    """
    Return a file as an encrypted text stream that is decrypted by the client.
    Proxies and firewalls cannot inspect the content type, the filename or the file content.
    """
    response = StreamingHttpResponseAsync(
        streaming_content=encrypted_stream(file=file, key=key, metadata={
            'version': FORMAT_VERSION,
            'cipher': 'AES-GCM',
            'filename': filename,
            'content_type': content_type,
        }),
        content_type='text/plain; charset=utf-8',
        headers=(headers or {}) | {
            'Content-Disposition': 'attachment',
            # Encrypted responses must never be cached: the ciphertext is only valid for the key of this request.
            'Cache-Control': 'no-store',
        },
    )
    response.is_encrypted_download = True
    return response


def cache_control_plaintext(**kwargs):
    """
    Like Django's cache_control decorator, but skips encrypted downloads.
    Their response must stay uncacheable, because the ciphertext is only valid for the key of one request.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **view_kwargs):
            response = view_func(request, *args, **view_kwargs)
            if not getattr(response, 'is_encrypted_download', False):
                patch_cache_control(response, **kwargs)
            return response
        return _wrapped_view
    return decorator
