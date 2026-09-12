from django.core.cache import cache

from .models import Membership


class MembershipCache:
    ttl = 300

    @classmethod
    def _key(cls, conversation_id):
        return f"kozons:v1:conversation:{conversation_id}:active_members"

    @classmethod
    def get_user_ids(cls, conversation_id):
        key = cls._key(conversation_id)
        values = cache.get(key)
        if values is None:
            values = list(
                Membership.objects.filter(
                    conversation_id=conversation_id,
                    utilisateur__is_active=True,
                ).values_list("utilisateur_id", flat=True)
            )
            cache.set(key, values, timeout=cls.ttl)
        return values

    @classmethod
    def invalidate(cls, conversation_id):
        cache.delete(cls._key(conversation_id))
