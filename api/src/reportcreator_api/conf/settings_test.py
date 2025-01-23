from reportcreator_api.conf.settings import *  # noqa: F403
from reportcreator_api.conf.settings import (
    ENABLED_PLUGINS,
    INSTALLED_APPS,
    PLUGIN_DIRS,
    REST_FRAMEWORK,
    STORAGES,
    load_plugins,
)

STORAGES = STORAGES | {
    'uploadedimages': {'BACKEND': 'django.core.files.storage.InMemoryStorage'},
    'uploadedassets': {'BACKEND': 'django.core.files.storage.InMemoryStorage'},
    'uploadedfiles': {'BACKEND': 'django.core.files.storage.InMemoryStorage'},
    'archivedfiles': {'BACKEND': 'django.core.files.storage.InMemoryStorage'},
}
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
}
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

REST_FRAMEWORK |= {
    'DEFAULT_THROTTLE_CLASSES': [],
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}


ALLOWED_HOSTS = ['*']
CSRF_TRUSTED_ORIGINS = ['http://*', 'https://*']
MFA_FIDO2_RP_ID=''


LOCAL_USER_AUTH_ENABLED = True
REMOTE_USER_AUTH_ENABLED = True
REMOTE_USER_AUTH_HEADER = 'Remote-User'
AUTHLIB_OAUTH_CLIENTS = {}


ELASTIC_APM_ENABLED = False
ELASTIC_APM_RUM_ENABLED = False
CELERY_TASK_ALWAYS_EAGER = True
NOTIFICATION_IMPORT_URL = None


GUEST_USERS_CAN_EDIT_PROJECTS = True
GUEST_USERS_CAN_UPDATE_PROJECT_SETTINGS = True
GUEST_USERS_CAN_CREATE_PROJECTS = True
GUEST_USERS_CAN_DELETE_PROJECTS = True
GUEST_USERS_CAN_IMPORT_PROJECTS = False
GUEST_USERS_CAN_SEE_ALL_USERS = False
GUEST_USERS_CAN_SHARE_NOTES = False
PROJECT_MEMBERS_CAN_ARCHIVE_PROJECTS = True


ENABLE_PRIVATE_DESIGNS = True
DISABLE_SHARING = False
SHARING_PASSWORD_REQUIRED = False
SHARING_READONLY_REQUIRED = False
ARCHIVING_THRESHOLD = 1
AUTOMATICALLY_ARCHIVE_PROJECTS_AFTER = None
AUTO_DELETE_ARCHIVE_AFTER = None

PREFERRED_LANGUAGES = ['en-US', 'de-DE']

INSTALLATION_ID = 'dummy-installation-id-used-in-unit-test'
BACKUP_KEY = 'dummy-backup-key-used-in-unit-test'


# Disable license check
from reportcreator_api.conf import plugins  # noqa: E402
from reportcreator_api.utils import license  # noqa: E402

license.check_license = lambda **kwargs: {'type': license.LicenseType.PROFESSIONAL, 'users': 1000, 'name': 'Company Name'}
plugins.can_load_professional_plugins = lambda: True


# Always enable some plugins during tests
ENABLED_PLUGINS += ['demoplugin']
enable_test_plugins = load_plugins(PLUGIN_DIRS, ENABLED_PLUGINS)
INSTALLED_APPS += [p for p in enable_test_plugins if p not in INSTALLED_APPS]
