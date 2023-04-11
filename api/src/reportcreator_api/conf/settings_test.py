from reportcreator_api.conf.settings import *
from reportcreator_api.utils.utils import merge


STORAGES = merge(STORAGES, {
    'uploaded_images': {'BACKEND': 'reportcreator_api.utils.storages.EncryptedInMemoryStorage'},
    'uploaded_assets': {'BACKEND': 'reportcreator_api.utils.storages.EncryptedInMemoryStorage'},
    'uploaded_files': {'BACKEND': 'reportcreator_api.utils.storages.EncryptedInMemoryStorage'},
})


REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []
REST_FRAMEWORK['TEST_REQUEST_DEFAULT_FORMAT'] = 'json'


AUTHLIB_OAUTH_CLIENTS = {}
ELASTIC_APM_ENABLED = False
ELASTIC_APM_RUM_ENABLED = False
CELERY_TASK_ALWAYS_EAGER = True
NOTIFICATION_IMPORT_URL = None


ENABLE_PRIVATE_DESIGNS = True
