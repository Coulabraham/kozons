from datetime import datetime, timezone

from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


class RevocableJWTAuthentication(JWTAuthentication):
    """Révoque aussi les access tokens émis avant une invalidation globale."""

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if validated_token.get("ver") != user.token_version:
            raise AuthenticationFailed("Ce jeton a été révoqué.", code="token_revoked")
        issued_at = validated_token.get("iat")
        if user.tokens_valid_after and issued_at:
            issued = datetime.fromtimestamp(int(issued_at), tz=timezone.utc)
            if issued < user.tokens_valid_after:
                raise AuthenticationFailed("Ce jeton a été révoqué.", code="token_revoked")
        return user
