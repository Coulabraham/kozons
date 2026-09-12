"""Profil local autonome, sans seed, pour développer Kozons sans Docker."""

import os
import ipaddress
import socket
from urllib.parse import urlparse

from .base import *  # noqa: F403


DEBUG = True
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "unsafe-local-only-kozons-secret-key-never-use-in-production",
)


def private_network_origins():
    try:
        addresses = socket.gethostbyname_ex(socket.gethostname())[2]
    except OSError:
        return []
    return [
        f"http://{address}:3000"
        for address in addresses
        if ipaddress.ip_address(address).is_private and not ipaddress.ip_address(address).is_loopback
    ]


LOCAL_NETWORK_ORIGINS = list(dict.fromkeys([  # noqa: F405
    *env_list("KOZONS_LOCAL_NETWORK_ORIGINS"),
    *private_network_origins(),
]))
LOCAL_NETWORK_HOSTS = [
    hostname
    for origin in LOCAL_NETWORK_ORIGINS
    if (hostname := urlparse(origin).hostname)
]
ALLOWED_HOSTS = ["localhost", "127.0.0.1", *LOCAL_NETWORK_HOSTS]
CORS_ALLOWED_ORIGINS = [*CORS_ALLOWED_ORIGINS, *LOCAL_NETWORK_ORIGINS]  # noqa: F405
CSRF_TRUSTED_ORIGINS = [*CSRF_TRUSTED_ORIGINS, *LOCAL_NETWORK_ORIGINS]  # noqa: F405
WEBSOCKET_ALLOWED_ORIGINS = [*WEBSOCKET_ALLOWED_ORIGINS, *LOCAL_NETWORK_ORIGINS]  # noqa: F405
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "kozons-local.sqlite3",  # noqa: F405
    }
}
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
PRESENCE_REDIS_ENABLED = False
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
OTP_FIXED_CODE = (
    None
    if env_bool("KOZONS_USE_RANDOM_OTP", False)  # noqa: F405
    else os.getenv("OTP_FIXED_CODE", "000000")
)
MEDIA_USE_FAKE_PRESIGN = True
CLAMAV_ENABLED = False

SIMPLE_JWT["SIGNING_KEY"] = os.getenv("JWT_SIGNING_KEY") or SECRET_KEY  # noqa: F405
RATE_LIMIT_SECRET = os.getenv("RATE_LIMIT_SECRET") or SECRET_KEY  # noqa: F405
MEDIA_PATH_HMAC_SECRET = os.getenv("MEDIA_PATH_HMAC_SECRET") or SECRET_KEY  # noqa: F405
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
JWT_REFRESH_COOKIE_SECURE = False
WEBSOCKET_ALLOW_QUERY_TOKEN = True
