import hashlib
from base64 import b64decode
from uuid import UUID

from django.contrib.auth.hashers import BasePasswordHasher, mask_hash
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from rest_framework import authentication, exceptions

from sysreptor.users.roles import Permission, expand_permissions
from sysreptor.utils import license


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
        return f"sha3_256$${hash}"

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

    def parse_apitoken(self, request):
        """
        Decode the Bearer header and fetch the token row.
        """
        from sysreptor.users.models import APIToken

        auth = authentication.get_authorization_header(request).split()
        if not auth or auth[0].lower() != b'bearer':
            request._apitoken_lookup = None
            return None

        try:
            if len(auth) != 2:
                raise Exception()
            if not auth[1].startswith(APIToken.TOKEN_PREFIX.encode()):
                raise Exception()
            token_id, token_key = b64decode(auth[1][len(APIToken.TOKEN_PREFIX.encode()):]).decode().split(':')
            token_id = UUID(token_id)
        except Exception as ex:
            # Do not cache malformed headers: AuthenticationFailed must be raised every time.
            raise exceptions.AuthenticationFailed('Invalid token header format.') from ex

        token = APIToken.objects \
            .select_related('user') \
            .defer('user__password') \
            .filter(id=token_id) \
            .first() or APIToken()

        # always validate token to prevent timing attacks (even if it does not exist)
        if not token.validate_token(token_key):
            raise exceptions.AuthenticationFailed('Invalid API token')

        return token

    def validate_token(self, token):
        if not token.user.is_active:
            raise exceptions.AuthenticationFailed('User disabled or deleted.')
        if token.expire_date and token.expire_date < timezone.now().date():
            raise exceptions.AuthenticationFailed('API token expired')
        if token.is_restricted and not license.is_professional():
            raise exceptions.AuthenticationFailed('Restricted API tokens require a Professional license.')
        license.validate_login_allowed(token.user)

    def update_apitoken_last_used(self, token):
        if not token.last_used or token.last_used < timezone.now() - timezone.timedelta(minutes=5):
            token.last_used = timezone.now()
            token.save(update_fields=['last_used'])

    def authenticate(self, request):
        token = self.parse_apitoken(request)
        if not token:
            return None

        self.validate_token(token)
        user = token.user
        user.api_token = token

        if token.is_restricted:
            view = (request.parser_context or {}).get('view')
            if not getattr(view, 'allow_restricted_api_token', False):
                raise exceptions.PermissionDenied(
                    detail='This operation is not permitted with a restricted API token.',
                    code='permission_denied_with_restricted_apitoken',
                )

            # Strip privileged roles for this request only. Do not persist these changes.
            user.admin_permissions_enabled = False

            # Restrict permissions to the API token's allow-list
            perms = expand_permissions(token.permissions if token.permissions is not None else user.effective_permissions)
            if token.is_project_restricted:
                # Project allow-list must never grant cross-project access
                perms = perms - {Permission.ADMIN_ACCESS_ALL_PROJECTS}
            user.restrict_permissions(perms)
        elif user.is_superuser and token.admin_permissions_enabled:
            user.admin_permissions_enabled = True

        self.update_apitoken_last_used(token)
        return user, token

    def authenticate_header(self, request):
        return self.keyword


def forbidden_with_apitoken_auth(request):
    from sysreptor.users.models import APIToken
    if isinstance(request.auth, APIToken):
        raise exceptions.PermissionDenied(
            detail='This operation is not permitted with API Token authentication. Log in to the web user interface.',
            code='permission_denied_with_apitoken_auth',
        )
    return True


def get_api_token(request_or_user):
    from sysreptor.users.models import APIToken, PentestUser
    if isinstance(request_or_user, PentestUser):
        return getattr(request_or_user, 'api_token', None)
    elif isinstance(request_or_user.auth, APIToken):
        return request_or_user.auth
    return None


def is_restricted_api_token(request_or_user):
    token = get_api_token(request_or_user)
    return bool(token and token.is_restricted)


def is_project_api_token(request_or_user):
    token = get_api_token(request_or_user)
    return bool(token and token.is_project_restricted)
