import unicodedata

from rest_framework.exceptions import ValidationError


MAX_MESSAGE_LENGTH = 10_000


def normalize_message_text(value):
    if value is None:
        return None
    normalized = unicodedata.normalize("NFC", str(value))
    if any(unicodedata.category(char) == "Cc" and char not in "\n\t" for char in normalized):
        raise ValidationError("Le message contient des caractères de contrôle interdits.")
    normalized = normalized.strip()
    if len(normalized) > MAX_MESSAGE_LENGTH:
        raise ValidationError(f"Le message ne peut pas dépasser {MAX_MESSAGE_LENGTH} caractères.")
    return normalized
