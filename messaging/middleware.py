from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from users.authentication import RevocableJWTAuthentication


@database_sync_to_async
def _authenticate(raw_token):
    authentication = RevocableJWTAuthentication()
    try:
        validated_token = authentication.get_validated_token(raw_token)
        return authentication.get_user(validated_token)
    except (AuthenticationFailed, InvalidToken, TokenError):
        return AnonymousUser()


class JWTAuthMiddleware:
    """JWT via Authorization ou sous-protocole; query string seulement en dev/test."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        token = None
        headers = dict(scope.get("headers", []))
        authorization = headers.get(b"authorization", b"").decode()
        if authorization.lower().startswith("bearer "):
            token = authorization.split(" ", 1)[1]
        for protocol in scope.get("subprotocols", []):
            if protocol.startswith("kozons.jwt."):
                token = protocol.removeprefix("kozons.jwt.")
                scope["accepted_subprotocol"] = "kozons"
                break
        if not token and settings.WEBSOCKET_ALLOW_QUERY_TOKEN:
            query = parse_qs(scope.get("query_string", b"").decode())
            token = query.get("token", [None])[0]
        scope["user"] = await _authenticate(token) if token else AnonymousUser()
        return await self.app(scope, receive, send)
