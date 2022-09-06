"""
WSGI config for reportcreator_api project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/wsgi/
"""

import os

from pathlib import Path
from whitenoise import WhiteNoise
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reportcreator_api.settings')


application = get_wsgi_application()

# Serve static frontend files
BASE_DIR = Path(__file__).resolve().parent.parent
# Serve SPA frontend files (generated JS files)
application = WhiteNoise(application, root=BASE_DIR / 'frontend')
# Serve django static files (required by admin and API browser)
application = WhiteNoise(application, prefix='/static/', root=BASE_DIR / 'static')
