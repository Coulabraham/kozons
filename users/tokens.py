from datetime import datetime, timezone as dt_timezone

from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


def assert_same_site_request(request):
    if request.headers.get("Sec-Fetch-Site") == "cross-site":
        raise PermissionDenied("Requête intersite refusée.")
    origin = request.headers.get("Origin")
    if origin and origin not in settings.CORS_ALLOWED_ORIGINS:
        raise PermissionDenied("Origine non autorisée.")


def set_refresh_cookie(response, refresh):
    response.set_cookie(
        settings.JWT_REFRESH_COOKIE_NAME,
        refresh,
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        path="/api/auth/",
        secure=settings.JWT_REFRESH_COOKIE_SECURE,
        httponly=True,
        samesite=settings.JWT_REFRESH_COOKIE_SAMESITE,
    )


def clear_refresh_cookie(response):
    response.delete_cookie(
        settings.JWT_REFRESH_COOKIE_NAME,
        path="/api/auth/",
        samesite=settings.JWT_REFRESH_COOKIE_SAMESITE,
    )


def token_is_current(user, token):
    if token.get("ver") != user.token_version:
        return False
    if not user.tokens_valid_after:
        return True
    issued_at = datetime.fromtimestamp(int(token["iat"]), tz=dt_timezone.utc)
    return issued_at >= user.tokens_valid_after


class CookieTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        token = RefreshToken(attrs["refresh"])
        try:
            user = User.objects.get(pk=token[api_settings.USER_ID_CLAIM])
        except User.DoesNotExist as exc:
            raise AuthenticationFailed("Utilisateur introuvable.") from exc
        if not user.is_active or not token_is_current(user, token):
            raise AuthenticationFailed("Ce jeton a été révoqué.")
        return super().validate(attrs)


def issue_refresh_token(user):
    refresh = RefreshToken.for_user(user)
    refresh["ver"] = user.token_version
    return refresh


def revoke_all_tokens(user):
    for outstanding in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=outstanding)
    user.tokens_valid_after = timezone.now()
    user.token_version += 1
    user.save(update_fields=["tokens_valid_after", "token_version"])
