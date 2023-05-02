import base64
import dataclasses
import enum
import io
import json
from typing import Optional
from Cryptodome.Cipher import AES
from Cryptodome.Cipher._mode_gcm import _GHASH, _ghash_clmul, _ghash_portable
from Cryptodome.Util.number import long_to_bytes, bytes_to_long

from django.conf import settings
from django.core.files.utils import FileProxyMixin


# Magic bytes to identify encrypted data
# Invalid UTF-8, such that an error occurs when someone tries to load encrypted data as text
MAGIC = b'\xC2YPT'


class CryptoError(Exception):
    pass


class EncryptionCipher(enum.Enum):
    AES_GCM = 'AES-GCM'


@dataclasses.dataclass
class EncryptionKey:
    id: str
    key: bytes
    cipher: EncryptionCipher = EncryptionCipher.AES_GCM
    revoked: bool = False

    @classmethod
    def from_json_list(cls, data: str) -> dict:
        if not data:
            return {}
        return dict(map(lambda e: (e['id'], cls(**(e | {
            'cipher': EncryptionCipher(e['cipher']),
            'key': base64.b64decode(e['key']),
        }))), json.loads(data)))
    

class ReadIntoAdapter(FileProxyMixin):
    def __init__(self, file) -> None:
        self.file = file

    def readinto(self, b):
        r = self.file.read(len(b))
        b[0:len(r)] = r
        return len(r)


def open(fileobj, mode='r', **kwargs):
    plaintext_fallback = kwargs.get('plaintext_fallback', settings.ENCRYPTION_PLAINTEXT_FALLBACK)

    if mode in ['r', 'rb']:
        key = kwargs.pop('key', None)
        keys = kwargs.pop('keys', settings.ENCRYPTION_KEYS)

        if not hasattr(fileobj, 'readinto'):
            fileobj = ReadIntoAdapter(fileobj)
        if not hasattr(fileobj, 'peek'):
            fileobj = io.BufferedReader(fileobj)
        if fileobj.peek(len(MAGIC)).startswith(MAGIC):
            return DecryptionStream(fileobj=fileobj, key=key, keys=keys, **kwargs)
        elif plaintext_fallback:
            return BufferedReaderNonClosing(fileobj)
        else:
            raise CryptoError('Data is not encrypted and plaintext fallback is disabled')
    elif mode in ['w', 'wb']:
        key_id = kwargs.pop('key_id', settings.DEFAULT_ENCRYPTION_KEY_ID)
        key = kwargs.pop('key', settings.ENCRYPTION_KEYS.get(key_id))

        if key:
            return EncryptionStream(fileobj, key=key, **kwargs)
        elif plaintext_fallback:
            return BufferedWriterNonClosing(fileobj)
        else:
            raise CryptoError('No key provided and plaintext fallback is disabled')


def readexact(fileobj, size):
    out = b''
    while len(out) < size:
        chunk = fileobj.read(size - len(out))
        if not chunk:
            raise CryptoError('Data missing on stream. Cannot read desired amount of data.')
        out += chunk
    return out


def readall(fileobj):
    out = b''
    while chunk := fileobj.read():
        out += chunk
    return out


class NonClosingBufferedIOMixin:
    """
    BufferedReader that does not close the underlying raw stream when the reader gets closed.
    """
    def close(self):
        if self.raw is not None and not self.closed:
            # may raise BlockingIOError or BrokenPipeError etc
            self.flush()

class BufferedReaderNonClosing(NonClosingBufferedIOMixin, io.BufferedReader):
    pass


class BufferedWriterNonClosing(NonClosingBufferedIOMixin, io.BufferedWriter):
    pass


class EncryptionStream(io.RawIOBase):
    def __init__(self, fileobj, key: EncryptionKey, nonce=None) -> None:
        self.fileobj = fileobj
        self.header_written = False
        self.key = key
        self.cipher = self._init_cipher(nonce=nonce)
        
    def readable(self) -> bool:
        return False

    def writable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return False

    def _init_cipher(self, nonce=None):
        if self.key.revoked:
            raise CryptoError('Key is revoked. It cannot be used for encryption anymore.')
        if self.key.cipher == EncryptionCipher.AES_GCM:
            return AES.new(key=self.key.key, mode=AES.MODE_GCM, nonce=nonce)
        else:
            raise CryptoError('Unknown cipher')

    def _ensure_header(self):
        if self.header_written:
            return

        # Write header at start of file before any data
        header = MAGIC + json.dumps({
            'cipher': self.key.cipher.value,
            'nonce': base64.b64encode(self.cipher.nonce).decode(),
            'key_id': self.key.id,
        }).encode() + b'\x00'
        self.fileobj.write(header)

        # Add header to authentication data. Modifications in header will be detected by authentication tag.
        self.cipher.update(header)
        self.header_written = True

    def write(self, data: bytes):
        if self.closed:
            raise ValueError('write() on closed stream')
        
        # Encrypt data
        self._ensure_header()
        self.fileobj.write(self.cipher.encrypt(data))

    def flush(self) -> None:
        return self.fileobj.flush()

    def close(self):
        if self.closed:
            return
        try:
            # Write authentication tag at end
            self._ensure_header()
            tag = self.cipher.digest()
            self.fileobj.write(tag)
        finally:
            super().close()
        

class DecryptionStream(io.RawIOBase):
    def __init__(self, fileobj, key: Optional[EncryptionKey] = None, keys: Optional[dict[str, EncryptionKey]] = None) -> None:
        self.fileobj = fileobj
        self.metdata = None
        self.cipher = None
        self.header_len = 0
        self.auth_tag_len = 16
        self.auth_tag_buffer = bytearray()
        self.auth_tag_verified = False

        self._load_header(key=key, keys=keys)

    def readable(self) -> bool:
        return True
    
    def writable(self) -> bool:
        return False

    def seekable(self) -> bool:
        return self.fileobj.seekable() and self.metadata['cipher'] == EncryptionCipher.AES_GCM

    def _load_header(self, key=None, keys=None):
        # Check magic
        if self.fileobj.read(len(MAGIC)) != MAGIC:
            raise CryptoError('Invalid header: magic not found')
        
        # Read metadata
        metadata_buffer = bytearray()
        while True:
            b = self.fileobj.read(1)
            if not b:
                raise CryptoError('Invalid header: missing or corrupted metadata')
            elif b == b'\x00':
                break
            else:
                metadata_buffer.extend(b)
        
        # Decode metadata
        try:
            self.metadata = json.loads(metadata_buffer)
            self.metadata['cipher'] = EncryptionCipher(self.metadata['cipher'])
            self.metadata['nonce'] = base64.b64decode(self.metadata['nonce'])

            if key:
                self.metadata['key'] = key
            elif keys:
                self.metadata['key'] = keys.get(self.metadata['key_id'])
            else:
                raise CryptoError('Either a key or a multiple available keys must be given')
        except CryptoError as ex:
            raise
        except Exception as ex:
            raise CryptoError('Failed to load metadata') from ex

        # Check metadata
        if not self.metadata['key']:
            raise CryptoError('Metadata contains unknown key_id. Cannot find a suitable key for decryption.')
        if self.metadata['key'].revoked:
            raise CryptoError('Key was revoked and cannot be used for decryption anymore.')

        # Initialize cipher
        try:
            if self.metadata['key'].cipher == EncryptionCipher.AES_GCM:
                self.cipher = AES.new(
                    mode=AES.MODE_GCM, 
                    key=self.metadata['key'].key, 
                    nonce=self.metadata['nonce']
                )
            else:
                raise CryptoError('Unsupported cipher')
        except Exception as ex:
            raise CryptoError('Error initializing cipher') from ex

        # Add header to auth tag
        header = MAGIC + metadata_buffer + b'\x00'
        self.header_len = len(header)
        self.cipher.update(header)

        # Buffer auth tag at end
        self.auth_tag_buffer.extend(readexact(self.fileobj, self.auth_tag_len))

    def read(self, size=-1):
        # Decrypt data (except auth tag at end of stream)
        self.auth_tag_buffer.extend(self.fileobj.read(size))
        res = self.auth_tag_buffer[:-self.auth_tag_len]
        del self.auth_tag_buffer[:-self.auth_tag_len]
        return self.cipher.decrypt(res)
    
    def readinto(self, buf) -> int:
        val = self.read(len(buf))
        buf[:len(val)] = val
        return len(val)

    def tell(self) -> int:
        return self.fileobj.tell() - self.header_len - len(self.auth_tag_buffer)

    def seek(self, offset: int, whence=io.SEEK_SET) -> int:
        if not self.seekable():
            raise io.UnsupportedOperation()

        if whence not in [io.SEEK_SET, io.SEEK_END]:
            return self.tell()

        # AEAD cipher modes support only linear decryption, no seeking
        # In order to be able to change the position, we first verify the auth tag to ensure that the ciphertext was not modified
        self._verify_auth_tag()
        self.auth_tag_buffer.clear()

        # Then seek to the desired position in the file
        if whence == io.SEEK_SET:
            pos_absolute = self.fileobj.seek(offset + self.header_len, whence)
        elif whence == io.SEEK_END:
            pos_absolute = self.fileobj.seek(0, whence)
            pos_absolute = self.fileobj.seek(pos_absolute - self.auth_tag_len, io.SEEK_SET)

        # Algin position in ciphertext to cipher blocks
        pos_in_ciphertext = pos_absolute - self.header_len
        num_blocks_skip = pos_in_ciphertext // self.cipher.block_size
        align_block_skip = pos_in_ciphertext % self.cipher.block_size
        self.fileobj.seek(pos_absolute - align_block_skip, io.SEEK_SET)

        # Then we can use a regular CTR mode for decryption. CTR mode supports encrypting/decrypting arbitrary blocks.
        # We need to initialize the CTR mode with the correct nonce/IV. They need to calculated the same way as for the GCM mode.
        self.cipher = self._init_seek_cipher_aes_gcm(key=self.metadata['key'].key, nonce=self.metadata['nonce'], skip_blocks=num_blocks_skip)

        # Finally can move from the block boundary to the final position
        self.auth_tag_buffer.clear()
        self.auth_tag_buffer.extend(readexact(self.fileobj, self.auth_tag_len))
        self.read(align_block_skip)

        return self.tell()

    def _init_seek_cipher_aes_gcm(self, key, nonce, skip_blocks):
        """
        Initialized a new AES CTR cipher at a given block offset.
        Counter calculation is compatible with AES GCM.
        GCM CTR cipher initialized code is taken from Cryptodome.Cipher._mode_gcm.GcmMode.__init__
        """
        # Step 1 in SP800-38D, Algorithm 4 (encryption) - Compute H
        # See also Algorithm 5 (decryption)
        hash_subkey = AES.new(mode=AES.MODE_ECB, key=key).encrypt(b'\x00' * 16)

        # Step 2 - Compute J0
        if len(nonce) == 12:
            j0 = nonce + b"\x00\x00\x00\x01"
        else:
            fill = (16 - (len(nonce) % 16)) % 16 + 8
            ghash_in = (nonce +
                        b'\x00' * fill +
                        long_to_bytes(8 * len(nonce), 8))
            j0 = _GHASH(hash_subkey, _ghash_clmul or _ghash_portable).update(ghash_in).digest()
        
        # Step 3 - Prepare GCTR cipher for encryption/decryption
        nonce_ctr = j0[:12]
        iv_ctr = (bytes_to_long(j0) + 1 + skip_blocks) & 0xFFFFFFFF
        return AES.new(
            mode=AES.MODE_CTR, 
            key=key, 
            initial_value=iv_ctr, 
            nonce=nonce_ctr)

    def _verify_auth_tag(self):
        if self.auth_tag_verified:
            return

        try:
            # Read everything to update the internal auth tag calculation
            while _ := self.read():
                pass
            
            self.cipher.verify(self.auth_tag_buffer)
            self.auth_tag_verified = True
        except Exception as ex:
            raise CryptoError('Auth tag verification failed') from ex

    def close(self):
        try:
            self._verify_auth_tag()
        finally:
            super().close()


