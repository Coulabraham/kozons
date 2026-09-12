import json

from celery import shared_task
from django.conf import settings
from pywebpush import WebPushException, webpush


@shared_task
def notify_offline_recipients_task(message_id):
    from messaging.models import Message
    from messaging.presence import PresenceService

    try:
        message = Message.objects.select_related("utilisateur_expediteur").get(pk=message_id)
    except Message.DoesNotExist:
        return
    recipient_ids = message.statuts.values_list("utilisateur_id", flat=True)
    for user_id in recipient_ids:
        if not PresenceService.is_online(user_id):
            send_message_push_task.delay(user_id, message_id)


@shared_task(
    autoretry_for=(OSError,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def send_message_push_task(user_id, message_id):
    if not settings.VAPID_PRIVATE_KEY:
        return
    from messaging.models import Message

    from .models import PushSubscription

    try:
        message = Message.objects.select_related("utilisateur_expediteur").get(pk=message_id)
    except Message.DoesNotExist:
        return
    payload = json.dumps(
        {
            "type": "message.new",
            "conversation_id": message.conversation_id,
            "message_id": message.id,
            "sender": message.utilisateur_expediteur.nom_affichage,
        }
    )
    for subscription in PushSubscription.objects.filter(utilisateur_id=user_id, actif=True):
        try:
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
                },
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": f"mailto:{settings.VAPID_ADMIN_EMAIL}"},
                ttl=300,
            )
        except WebPushException as exc:
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            if status_code in {404, 410}:
                subscription.actif = False
                subscription.save(update_fields=["actif", "date_maj"])
            else:
                raise
