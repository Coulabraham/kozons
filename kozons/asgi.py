"""Entrée ASGI : HTTP Django et WebSocket Channels."""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kozons.settings.dev")

from django.core.asgi import get_asgi_application

django_asgi_application = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import OriginValidator
from django.conf import settings

from messaging.middleware import JWTAuthMiddleware
from messaging.routing import websocket_urlpatterns

application = ProtocolTypeRouter(
    {
        "http": django_asgi_application,
        "websocket": OriginValidator(
            JWTAuthMiddleware(URLRouter(websocket_urlpatterns))
            , settings.WEBSOCKET_ALLOWED_ORIGINS
        ),
    }
)
