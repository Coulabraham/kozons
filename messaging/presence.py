import json
import time

from django.conf import settings
from django.core.cache import cache


class PresenceService:
    connection_ttl = 60

    @classmethod
    def _connection_key(cls, user_id):
        return f"kozons:v1:presence:user:{user_id}:connections"

    @classmethod
    def _status_key(cls, user_id):
        return f"kozons:v1:presence:user:{user_id}"

    @classmethod
    def _redis(cls):
        if not settings.PRESENCE_REDIS_ENABLED:
            return None
        try:
            import redis

            return redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        except (ImportError, OSError):
            return None

    @classmethod
    def heartbeat(cls, user_id, connection_id):
        client = cls._redis()
        now = int(time.time())
        if client is None:
            cache.set(cls._status_key(user_id), True, cls.connection_ttl)
            return True
        try:
            key = cls._connection_key(user_id)
            expires_at = now + cls.connection_ttl
            pipe = client.pipeline(transaction=True)
            pipe.zremrangebyscore(key, 0, now)
            pipe.zadd(key, {connection_id: expires_at})
            pipe.expire(key, cls.connection_ttl * 2)
            pipe.set(
                cls._status_key(user_id),
                json.dumps({"online": True, "heartbeat_at": now}),
                ex=cls.connection_ttl,
            )
            pipe.execute()
            return True
        except Exception:
            cache.set(cls._status_key(user_id), True, cls.connection_ttl)
            return True

    @classmethod
    def disconnect(cls, user_id, connection_id):
        client = cls._redis()
        if client is None:
            cache.delete(cls._status_key(user_id))
            return False
        try:
            key = cls._connection_key(user_id)
            now = int(time.time())
            pipe = client.pipeline(transaction=True)
            pipe.zrem(key, connection_id)
            pipe.zremrangebyscore(key, 0, now)
            pipe.zcard(key)
            results = pipe.execute()
            online = bool(results[-1])
            if not online:
                client.delete(cls._status_key(user_id))
            return online
        except Exception:
            cache.delete(cls._status_key(user_id))
            return False

    @classmethod
    def is_online(cls, user_id):
        client = cls._redis()
        if client is not None:
            try:
                return bool(client.exists(cls._status_key(user_id)))
            except Exception:
                pass
        return bool(cache.get(cls._status_key(user_id)))
