import hashlib
import hmac
import logging

from django.conf import settings

from .models import SecurityAuditEvent

logger = logging.getLogger("security.audit")


def _digest(value):
    if not value:
        return ""
    return hmac.new(settings.RATE_LIMIT_SECRET.encode(), str(value).encode(), hashlib.sha256).hexdigest()


def record_security_event(*, event, success, actor=None, ip=None, subject=None, metadata=None):
    safe_metadata = metadata or {}
    SecurityAuditEvent.objects.create(
        actor=actor,
        event=event,
        success=success,
        ip_hash=_digest(ip),
        subject_hash=_digest(subject),
        metadata=safe_metadata,
    )
    logger.info(
        "security_event=%s success=%s actor_id=%s ip_hash=%s subject_hash=%s metadata=%s",
        event,
        success,
        getattr(actor, "id", None),
        _digest(ip),
        _digest(subject),
        safe_metadata,
    )
