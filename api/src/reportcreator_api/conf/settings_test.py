from reportcreator_api.conf.settings import *


STORAGES = STORAGES | {
    'uploaded_images': {'BACKEND': 'django.core.files.storage.InMemoryStorage'},
    'uploaded_assets': {'BACKEND': 'django.core.files.storage.InMemoryStorage'},
    'uploaded_files': {'BACKEND': 'django.core.files.storage.InMemoryStorage'},
    'archived_files': {'BACKEND': 'django.core.files.storage.InMemoryStorage'},
}


REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []
REST_FRAMEWORK['TEST_REQUEST_DEFAULT_FORMAT'] = 'json'


LOCAL_USER_AUTH_ENABLED = True
REMOTE_USER_AUTH_ENABLED = True
REMOTE_USER_AUTH_HEADER = 'Remote-User'
AUTHLIB_OAUTH_CLIENTS = {}


ELASTIC_APM_ENABLED = False
ELASTIC_APM_RUM_ENABLED = False
CELERY_TASK_ALWAYS_EAGER = True
NOTIFICATION_IMPORT_URL = None

ENABLE_PRIVATE_DESIGNS = True
ARCHIVING_THRESHOLD = 1
AUTOMATICALLY_ARCHIVE_PROJECTS_AFTER = None
AUTO_DELETE_ARCHIVE_AFTER = None

PREFERRED_LANGUAGES = ['en-US', 'de-DE']

BACKUP_KEY = 'dummy-backup-key-used-in-unit-test'


# Disable license check
from reportcreator_api.utils import license
license.check_license = lambda: {'type': license.LicenseType.PROFESSIONAL, 'users': 1000}
