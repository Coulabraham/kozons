import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

DEBUG = True
if not SECRET_KEY:  # noqa: F405
    raise ImproperlyConfigured("DJANGO_SECRET_KEY doit être défini, même en développement")
SIMPLE_JWT["SIGNING_KEY"] = os.getenv("JWT_SIGNING_KEY") or SECRET_KEY  # noqa: F405
RATE_LIMIT_SECRET = os.getenv("RATE_LIMIT_SECRET") or SECRET_KEY  # noqa: F405
MEDIA_PATH_HMAC_SECRET = os.getenv("MEDIA_PATH_HMAC_SECRET") or SECRET_KEY  # noqa: F405
ALLOWED_HOSTS = ["*"]
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
JWT_REFRESH_COOKIE_SECURE = False
WEBSOCKET_ALLOW_QUERY_TOKEN = True
