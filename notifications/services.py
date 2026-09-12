from .models import PushSubscription


def register_push_subscription(*, user, endpoint, p256dh, auth):
    subscription, _ = PushSubscription.objects.update_or_create(
        endpoint=endpoint,
        defaults={
            "utilisateur": user,
            "p256dh": p256dh,
            "auth": auth,
            "actif": True,
        },
    )
    return subscription
