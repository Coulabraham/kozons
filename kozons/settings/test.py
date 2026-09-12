from .base import *  # noqa: F403

DEBUG = False
SECRET_KEY = "test-only-kozons-secret-key-at-least-32-bytes"
SIMPLE_JWT["SIGNING_KEY"] = SECRET_KEY  # noqa: F405
RATE_LIMIT_SECRET = "test-only-rate-limit-secret"
MEDIA_PATH_HMAC_SECRET = "test-only-media-path-secret"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
PRESENCE_REDIS_ENABLED = False
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
OTP_FIXED_CODE = "000000"
MEDIA_USE_FAKE_PRESIGN = True
VAPID_PRIVATE_KEY = ""
JWT_REFRESH_COOKIE_SECURE = False
CLAMAV_ENABLED = False
WEBSOCKET_ALLOW_QUERY_TOKEN = True
