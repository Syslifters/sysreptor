from contextlib import contextmanager
import tempfile
import gnupg

from reportcreator_api.archive.crypto.base import CryptoError


@contextmanager
def create_gpg():
    with tempfile.TemporaryDirectory() as d:
        gpg = gnupg.GPG(gnupghome=d)
        gpg.encoding = 'utf-8'
        yield gpg


def public_key_info(public_key: str):
    if not public_key:
        raise CryptoError('No public key provided')

    with create_gpg() as gpg:
        with tempfile.NamedTemporaryFile(mode='w') as f:
            f.write(public_key)
            f.flush() 
            res = gpg.scan_keys(f.name)
        if len(res) == 0:
            raise CryptoError('Invalid public key format')
        if len(res) != 1:
            raise CryptoError('Only 1 public key allowed')
        key_info = res[0]

        if key_info.get('type') != 'pub':
            raise CryptoError('Not a public key')
        encryption_key_info = next(filter(lambda s: s.get('type') == 'sub' and s.get('cap') == 'e', key_info['subkey_info'].values()), None)
        if not encryption_key_info:
            raise CryptoError('No encryption key provided')
        
        # Allowed encryption ciphers: RSA, ECDH, ElGamal with min. key size
        if encryption_key_info['algo'] not in ['1', '2', '16', '18']:
            raise CryptoError('Unsupported algorithm')
        if encryption_key_info['algo'] in ['1', '2', '16'] and int(encryption_key_info['length']) < 3072:
            raise CryptoError('Key length too short. The minimum supported RSA key size is 3072 bit')
        elif encryption_key_info['algo'] in ['18'] and int(encryption_key_info['length']) < 256:
            raise CryptoError('Key length too short. The minimum supported Elliptic Curve size is 256 bit')
        
        return key_info


def encrypt(data: bytes, public_key: str):
    with create_gpg() as gpg:
        res =  gpg.import_keys(public_key)
        enc = gpg.encrypt(data=data, recipients=[res.results[0]['fingerprint']], always_trust=True)
        if not enc.ok:
            raise CryptoError('Encryption failed')
        return enc.data.decode()

