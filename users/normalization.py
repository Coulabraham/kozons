import phonenumbers
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email


def normalize_phone(value):
    if not value:
        return None
    try:
        parsed = phonenumbers.parse(value, getattr(settings, "DEFAULT_PHONE_REGION", "SN"))
    except phonenumbers.NumberParseException as exc:
        raise ValidationError("Numéro de téléphone invalide.") from exc
    if not phonenumbers.is_valid_number(parsed):
        raise ValidationError("Numéro de téléphone invalide.")
    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


def normalize_email(value):
    if not value:
        return None
    value = value.strip().lower()
    validate_email(value)
    return value


def normalize_identifier(value):
    value = (value or "").strip()
    if "@" in value:
        return "email", normalize_email(value)
    return "telephone", normalize_phone(value)
