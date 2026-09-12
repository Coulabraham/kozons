import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import password_validation
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed, ValidationError

from kozons.rate_limit import enforce_rate_limit

from .models import OTPVerification, User
from .normalization import normalize_email, normalize_identifier, normalize_phone
from .tasks import send_otp_task
from .tokens import issue_refresh_token


_DUMMY_PASSWORD_HASH = make_password(secrets.token_urlsafe(32))


def _new_otp(user, channel, purpose):
    code = settings.OTP_FIXED_CODE or f"{secrets.randbelow(1_000_000):06d}"
    otp = OTPVerification.objects.create(
        user=user,
        channel=channel,
        purpose=purpose,
        code_hash=make_password(code),
        expires_at=timezone.now() + timedelta(seconds=settings.OTP_TTL_SECONDS),
    )
    destination = user.telephone if channel == OTPVerification.Channel.SMS else user.email
    transaction.on_commit(lambda: send_otp_task.delay(channel, destination, code))
    return otp


@transaction.atomic
def register_user(*, telephone=None, email=None, password, nom_affichage, ip_address="unknown"):
    try:
        telephone = normalize_phone(telephone)
        email = normalize_email(email)
    except DjangoValidationError as exc:
        raise ValidationError(exc.messages) from exc
    if not telephone and not email:
        raise ValidationError("Un téléphone ou un email est obligatoire.")
    identifier = telephone or email
    enforce_rate_limit("register-identity", identifier, limit=5, period_seconds=900)
    enforce_rate_limit("register-ip", ip_address, limit=20, period_seconds=3600)
    try:
        password_validation.validate_password(password)
    except DjangoValidationError as exc:
        raise ValidationError(exc.messages) from exc
    try:
        user = User.objects.create_user(
            telephone=telephone,
            email=email,
            password=password,
            nom_affichage=nom_affichage.strip(),
            is_active=False,
            statut=User.Statut.INACTIF,
        )
    except IntegrityError as exc:
        raise ValidationError("Un compte existe déjà avec cet identifiant.") from exc
    channel = OTPVerification.Channel.SMS if telephone else OTPVerification.Channel.EMAIL
    _new_otp(user, channel, OTPVerification.Purpose.REGISTRATION)
    return user


def verify_registration_otp(*, identifier, code, ip_address="unknown"):
    try:
        kind, normalized = normalize_identifier(identifier)
    except DjangoValidationError as exc:
        raise ValidationError("Code invalide ou expiré.") from exc
    enforce_rate_limit("otp-identity", normalized, limit=5, period_seconds=900)
    enforce_rate_limit("otp-ip", ip_address, limit=30, period_seconds=900)
    with transaction.atomic():
        try:
            user = User.objects.select_for_update().get(**{kind: normalized})
        except User.DoesNotExist as exc:
            raise ValidationError("Code invalide ou expiré.") from exc
        otp = (
            OTPVerification.objects.select_for_update()
            .filter(user=user, purpose=OTPVerification.Purpose.REGISTRATION, consumed_at__isnull=True)
            .order_by("-created_at")
            .first()
        )
        if not otp or not otp.is_usable or otp.attempts >= settings.OTP_MAX_ATTEMPTS:
            raise ValidationError("Code invalide ou expiré.")
        otp.attempts += 1
        verified = check_password(code, otp.code_hash)
        if not verified:
            otp.save(update_fields=["attempts"])
        else:
            otp.consumed_at = timezone.now()
            otp.save(update_fields=["attempts", "consumed_at"])
            user.is_active = True
            user.statut = User.Statut.ACTIF
            user.save(update_fields=["is_active", "statut"])
    if not verified:
        raise ValidationError("Code invalide ou expiré.")
    return user


def login_user(*, identifier, password, ip_address="unknown"):
    try:
        kind, normalized = normalize_identifier(identifier)
    except DjangoValidationError as exc:
        raise AuthenticationFailed("Identifiant ou mot de passe incorrect.") from exc
    enforce_rate_limit("login-identity", normalized, limit=10, period_seconds=900)
    enforce_rate_limit("login-ip", ip_address, limit=60, period_seconds=900)
    user = User.objects.filter(Q(**{kind: normalized})).first()
    password_ok = user.check_password(password) if user else check_password(password, _DUMMY_PASSWORD_HASH)
    if (
        not user
        or not password_ok
        or not user.is_active
        or user.statut != User.Statut.ACTIF
    ):
        raise AuthenticationFailed("Identifiant ou mot de passe incorrect.")
    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])
    refresh = issue_refresh_token(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}, user


@transaction.atomic
def resend_registration_otp(*, identifier, ip_address="unknown"):
    try:
        kind, normalized = normalize_identifier(identifier)
    except DjangoValidationError:
        return
    enforce_rate_limit("otp-send-identity", normalized, limit=3, period_seconds=900)
    enforce_rate_limit("otp-send-ip", ip_address, limit=20, period_seconds=3600)
    user = User.objects.select_for_update().filter(**{kind: normalized}).first()
    if not user or user.is_active:
        return
    channel = OTPVerification.Channel.SMS if kind == "telephone" else OTPVerification.Channel.EMAIL
    _new_otp(user, channel, OTPVerification.Purpose.REGISTRATION)


def update_profile(*, user, nom_affichage=None, statut_personnalise=None, avatar_media_id=None):
    fields = []
    if nom_affichage is not None:
        user.nom_affichage = nom_affichage.strip()
        fields.append("nom_affichage")
    if statut_personnalise is not None:
        user.statut_personnalise = statut_personnalise.strip()
        fields.append("statut_personnalise")
    if avatar_media_id is not None:
        from media.models import MediaAsset
        from media.storage import object_reference

        try:
            asset = MediaAsset.objects.get(
                pk=avatar_media_id,
                utilisateur=user,
                conversation__isnull=True,
                type=MediaAsset.Type.IMAGE,
                statut=MediaAsset.Status.PRET,
            )
        except MediaAsset.DoesNotExist as exc:
            raise ValidationError("La photo de profil n'est pas prête ou ne vous appartient pas.") from exc
        user.avatar_url = object_reference(asset.output_object_key or asset.source_object_key)
        fields.append("avatar_url")
    if fields:
        user.save(update_fields=fields)
    return user
