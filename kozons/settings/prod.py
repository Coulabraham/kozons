import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

if len(SECRET_KEY) < 50:  # noqa: F405
    raise ImproperlyConfigured("DJANGO_SECRET_KEY (50 caractères minimum) est obligatoire")

if not os.getenv("DATABASE_URL"):
    raise ImproperlyConfigured("DATABASE_URL est obligatoire en production")

if not os.getenv("DJANGO_ALLOWED_HOSTS"):
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS est obligatoire en production")

for secret_name in ("RATE_LIMIT_SECRET", "MEDIA_PATH_HMAC_SECRET", "JWT_SIGNING_KEY"):
    if len(os.getenv(secret_name, "")) < 32:
        raise ImproperlyConfigured(f"{secret_name} (32 caractères minimum) est obligatoire")

if not CORS_ALLOWED_ORIGINS or any(not origin.startswith("https://") for origin in CORS_ALLOWED_ORIGINS):  # noqa: F405
    raise ImproperlyConfigured("CORS_ALLOWED_ORIGINS doit contenir uniquement des origines HTTPS")

if not WEBSOCKET_ALLOWED_ORIGINS or any(not origin.startswith("https://") for origin in WEBSOCKET_ALLOWED_ORIGINS):  # noqa: F405
    raise ImproperlyConfigured("WEBSOCKET_ALLOWED_ORIGINS doit contenir uniquement des origines HTTPS")

if OTP_FIXED_CODE:  # noqa: F405
    raise ImproperlyConfigured("OTP_FIXED_CODE est interdit en production")

if SMS_PROVIDER == "users.sms.ConsoleSMSProvider":  # noqa: F405
    raise ImproperlyConfigured("Un fournisseur SMS réel est obligatoire en production")

if EMAIL_BACKEND == "django.core.mail.backends.console.EmailBackend":  # noqa: F405
    raise ImproperlyConfigured("Un backend e-mail réel est obligatoire en production")

if EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend" and not all(  # noqa: F405
    (EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, DEFAULT_FROM_EMAIL)
):
    raise ImproperlyConfigured("La configuration SMTP e-mail est incomplète")

if SMS_PROVIDER == "users.sms.TwilioSMSProvider" and not all(  # noqa: F405
    (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER)
):
    raise ImproperlyConfigured("La configuration SMS Twilio est incomplète")

if SMS_PROVIDER == "users.sms.AfricasTalkingSMSProvider" and not all(  # noqa: F405
    (AFRICASTALKING_USERNAME, AFRICASTALKING_API_KEY)
):
    raise ImproperlyConfigured("La configuration SMS Africa's Talking est incomplète")

DEBUG = False
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
JWT_REFRESH_COOKIE_SECURE = True
WEBSOCKET_ALLOW_QUERY_TOKEN = False
CLAMAV_ENABLED = env_bool("CLAMAV_ENABLED", True)  # noqa: F405
