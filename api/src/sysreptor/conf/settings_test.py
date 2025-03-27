from sysreptor.conf.settings import *  # noqa: F403
from sysreptor.conf.settings import (
    CONFIGURATION_DEFINITION_CORE,
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
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
EMAIL_HOST = 'localhost'

REST_FRAMEWORK |= {
    'DEFAULT_THROTTLE_CLASSES': [],
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}


ALLOWED_HOSTS = ['*']
CSRF_TRUSTED_ORIGINS = ['http://*', 'https://*']
MFA_FIDO2_RP_ID = ''

ENCRYPTION_KEYS = {}
DEFAULT_ENCRYPTION_KEY_ID = None
ENCRYPTION_PLAINTEXT_FALLBACK = True

ELASTIC_APM_ENABLED = False
ELASTIC_APM_RUM_ENABLED = False
CELERY_TASK_ALWAYS_EAGER = True
NOTIFICATION_IMPORT_URL = None
SPELLCHECK_URL = None

BACKUP_KEY = 'dummy-backup-key-used-in-unit-test'


# Use default configurations, do not load from environment variables
LOAD_CONFIGURATIONS_FROM_ENV = False
LOAD_CONFIGURATIONS_FROM_DB = True
# Override default values for tests
CONFIGURATION_DEFINITION_CORE['ENABLE_PRIVATE_DESIGNS'].default = True
CONFIGURATION_DEFINITION_CORE['ARCHIVING_THRESHOLD'].default = 1
CONFIGURATION_DEFINITION_CORE['FORGOT_PASSWORD_ENABLED'].default = True
CONFIGURATION_DEFINITION_CORE['INSTALLATION_ID'].default = 'dummy-installation-id-used-in-unit-test'


# Disable license check
from sysreptor.conf import plugins  # noqa: E402
from sysreptor.utils import license, mail  # noqa: E402

license.check_license = lambda **kwargs: {'type': license.LicenseType.PROFESSIONAL, 'users': 1000, 'name': 'Company Name'}
plugins.can_load_professional_plugins = lambda: True

# Use blocking mail sending for tests
mail.send_mail_in_background = mail.send_mail


# Always enable some plugins during tests
ENABLED_PLUGINS += ['demoplugin']
enable_test_plugins = load_plugins(PLUGIN_DIRS, ENABLED_PLUGINS)
INSTALLED_APPS += [p for p in enable_test_plugins if p not in INSTALLED_APPS]
