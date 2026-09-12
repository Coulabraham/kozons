import hashlib
import hmac
import time

from django.conf import settings
from django.core.cache import cache
from rest_framework.exceptions import Throttled


def client_ip(request):
    """REMOTE_ADDR est fiable lorsque le nombre de proxies DRF est configuré correctement."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    proxies = int(settings.REST_FRAMEWORK.get("NUM_PROXIES", 0))
    if forwarded and proxies:
        chain = [part.strip() for part in forwarded.split(",") if part.strip()]
        if len(chain) > proxies:
            return chain[-(proxies + 1)]
    return request.META.get("REMOTE_ADDR", "unknown")


def enforce_rate_limit(scope, subject, *, limit, period_seconds):
    digest = hmac.new(settings.RATE_LIMIT_SECRET.encode(), str(subject).encode(), hashlib.sha256).hexdigest()[:32]
    window = int(time.time()) // period_seconds
    key = f"kozons:ratelimit:{scope}:{digest}:{window}"
    count = 1 if cache.add(key, 1, timeout=period_seconds + 1) else cache.incr(key)
    if count > limit:
        retry_after = period_seconds - (int(time.time()) % period_seconds)
        raise Throttled(wait=max(1, retry_after), detail="Trop de tentatives. Réessayez plus tard.")
