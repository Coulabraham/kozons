from django.conf import settings
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import APIException, AuthenticationFailed, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.settings import api_settings

from kozons.rate_limit import client_ip

from .audit import record_security_event
from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    ResendOTPSerializer,
    UserSerializer,
    VerifyOTPSerializer,
)
from .services import (
    login_user,
    register_user,
    resend_registration_otp,
    update_profile,
    verify_registration_otp,
)
from .tokens import (
    CookieTokenRefreshSerializer,
    assert_same_site_request,
    clear_refresh_cookie,
    revoke_all_tokens,
    set_refresh_cookie,
)


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "register"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ip = client_ip(request)
        identifier = serializer.validated_data.get("telephone") or serializer.validated_data.get("email")
        try:
            user = register_user(**serializer.validated_data, ip_address=ip)
        except APIException:
            record_security_event(event="registration", success=False, ip=ip, subject=identifier)
            raise
        record_security_event(event="registration", success=True, actor=user, ip=ip, subject=identifier)
        return Response({"user": UserSerializer(user).data, "otp_required": True}, status=status.HTTP_201_CREATED)


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "otp"

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ip = client_ip(request)
        identifier = serializer.validated_data["identifier"]
        try:
            user = verify_registration_otp(**serializer.validated_data, ip_address=ip)
        except APIException:
            record_security_event(event="otp_verification", success=False, ip=ip, subject=identifier)
            raise
        record_security_event(event="otp_verification", success=True, actor=user, ip=ip, subject=identifier)
        return Response({"user": UserSerializer(user).data, "verified": True})


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "login"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ip = client_ip(request)
        identifier = serializer.validated_data["identifier"]
        try:
            tokens, user = login_user(**serializer.validated_data, ip_address=ip)
        except APIException:
            record_security_event(event="login", success=False, ip=ip, subject=identifier)
            raise
        response = Response({"access": tokens["access"], "user": UserSerializer(user).data})
        set_refresh_cookie(response, tokens["refresh"])
        record_security_event(event="login", success=True, actor=user, ip=ip, subject=identifier)
        return response


class RefreshView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth_session"

    def post(self, request):
        assert_same_site_request(request)
        raw_refresh = request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME)
        if not raw_refresh:
            raise AuthenticationFailed("Jeton de renouvellement absent.")
        serializer = CookieTokenRefreshSerializer(data={"refresh": raw_refresh})
        serializer.is_valid(raise_exception=True)
        token = RefreshToken(serializer.validated_data.get("refresh", raw_refresh))
        from .models import User

        user = User.objects.get(pk=token[api_settings.USER_ID_CLAIM])
        response = Response({"access": serializer.validated_data["access"], "user": UserSerializer(user).data})
        set_refresh_cookie(response, serializer.validated_data.get("refresh", raw_refresh))
        return response


class LogoutView(APIView):
    throttle_scope = "auth_session"

    def post(self, request):
        assert_same_site_request(request)
        raw_refresh = request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME)
        if raw_refresh:
            try:
                RefreshToken(raw_refresh).blacklist()
            except TokenError:
                pass
        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_refresh_cookie(response)
        record_security_event(event="logout", success=True, actor=request.user, ip=client_ip(request))
        return response


class LogoutAllView(APIView):
    throttle_scope = "auth_session"

    def post(self, request):
        assert_same_site_request(request)
        revoke_all_tokens(request.user)
        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_refresh_cookie(response)
        record_security_event(event="logout_all", success=True, actor=request.user, ip=client_ip(request))
        return response


class ChangePasswordView(APIView):
    throttle_scope = "auth_session"

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not request.user.check_password(serializer.validated_data["current_password"]):
            record_security_event(event="password_change", success=False, actor=request.user, ip=client_ip(request))
            raise AuthenticationFailed("Mot de passe actuel incorrect.")
        new_password = serializer.validated_data["new_password"]
        try:
            password_validation.validate_password(new_password, request.user)
        except DjangoValidationError as exc:
            raise ValidationError({"new_password": exc.messages}) from exc
        request.user.set_password(new_password)
        request.user.save(update_fields=["password"])
        revoke_all_tokens(request.user)
        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_refresh_cookie(response)
        record_security_event(event="password_change", success=True, actor=request.user, ip=client_ip(request))
        return response


class ResendOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "otp_send"

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        resend_registration_otp(**serializer.validated_data, ip_address=client_ip(request))
        return Response({"sent": True})


class ProfileView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = update_profile(user=request.user, **serializer.validated_data)
        record_security_event(event="profile_update", success=True, actor=user, ip=client_ip(request))
        return Response(UserSerializer(user).data)
