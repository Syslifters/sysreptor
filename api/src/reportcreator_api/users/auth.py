import hashlib
from base64 import b64decode
from uuid import UUID

from django.contrib.auth.hashers import BasePasswordHasher, mask_hash
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from rest_framework import authentication, exceptions

from reportcreator_api.utils import license


class UnsaltedSHA3_256PasswordHasher(BasePasswordHasher):
    """
    SHA3 256-bit password hash.
    Used to store API tokens, where regular password hashers are too expensive.
    """

    algorithm = "sha3_256"

    def salt(self):
        return ""

    def encode(self, password, salt):
        if salt != "":
            raise ValueError("salt must be empty.")
        hash = hashlib.sha3_256(password.encode()).hexdigest()
        return "sha3_256$$%s" % hash

    def decode(self, encoded):
        assert encoded.startswith("sha3_256$$")
        return {
            "algorithm": self.algorithm,
            "hash": encoded[6:],
            "salt": None,
        }

    def verify(self, password, encoded):
        encoded_2 = self.encode(password, "")
        return constant_time_compare(encoded, encoded_2)

    def safe_summary(self, encoded):
        decoded = self.decode(encoded)
        return {
            "algorithm": decoded["algorithm"],
            "hash": mask_hash(decoded["hash"]),
        }

    def harden_runtime(self, password, encoded):
        pass


class APITokenAuthentication(authentication.BaseAuthentication):
    keyword = 'Bearer'

    def authenticate(self, request):
        from reportcreator_api.users.models import APIToken

        auth = authentication.get_authorization_header(request).split()
        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None

        try:
            if len(auth) != 2:
                raise Exception()
            if not auth[1].startswith(b'sysreptor_'):
                raise Exception()
            token_id, token_key = b64decode(auth[1][10:]).decode().split(':')
            token_id = UUID(token_id)
        except Exception as ex:
            raise exceptions.AuthenticationFailed('Invalid token header format.') from ex

        token = APIToken.objects \
            .select_related('user') \
            .defer('user__password') \
            .filter(id=token_id) \
            .first() or APIToken()
        # always validate token to prevent timing attacks (even if it does not exist)
        if not token.validate_token(token_key):
            raise exceptions.AuthenticationFailed('Invalid API token')
        if not token.user.is_active:
            raise exceptions.AuthenticationFailed('User inactive or deleted.')
        if token.expire_date and token.expire_date < timezone.now().date():
            raise exceptions.AuthenticationFailed('API token expired')
        license.validate_login_allowed(token.user)

        # Always enable full permissions of user
        if token.user.is_superuser:
            token.user.admin_permissions_enabled = True

        return token.user, token

    def authenticate_header(self, request):
        return self.keyword


def forbidden_with_apitoken_auth(request):
    from reportcreator_api.users.models import APIToken
    if isinstance(request.auth, APIToken):
        raise exceptions.PermissionDenied(
            detail='This operation is not permitted with API Token authentication. Log in to the web user interface.',
            code='permission_denied_with_apitoken_auth',
        )
    return True
