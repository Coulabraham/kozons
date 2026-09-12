import uuid
from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from kozons.rate_limit import enforce_rate_limit

from conversations.cache import MembershipCache
from conversations.models import Conversation, Membership
from notifications.tasks import notify_offline_recipients_task

from .models import Message, MessageHiddenFor, MessageReaction, MessageReceipt
from .text import normalize_message_text


def message_event_payload(message):
    from media.storage import presigned_read_url

    deleted = message.supprime_pour_tous_le is not None
    return {
        "id": message.id,
        "client_id": str(message.client_id) if message.client_id else None,
        "conversation_id": message.conversation_id,
        "sender_id": message.utilisateur_expediteur_id,
        "type": message.type,
        "message_type": message.type,
        "contenu": None if deleted else message.contenu,
        "media_url": None if deleted else presigned_read_url(message.media_url),
        "duree": None if deleted else message.duree,
        "date_envoi": message.date_envoi.isoformat(),
        "modifie_le": message.modifie_le.isoformat() if message.modifie_le else None,
        "supprime_pour_tous_le": (
            message.supprime_pour_tous_le.isoformat() if message.supprime_pour_tous_le else None
        ),
        "transfere": message.conversation_origine_id is not None,
        "receipts": [
            {
                "user_id": receipt.utilisateur_id,
                "statut": receipt.statut,
                "date_maj": receipt.date_maj.isoformat(),
            }
            for receipt in message.statuts.all()
        ],
        "reactions": [
            {"user_id": reaction.utilisateur_id, "emoji": reaction.emoji}
            for reaction in message.reactions.all()
        ],
    }


def _publish_persistent_event(conversation_id, event_type, payload, user_ids=None):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"conversation.{conversation_id}",
        {"type": event_type, "payload": payload},
    )
    recipients = user_ids or MembershipCache.get_user_ids(conversation_id)
    for user_id in recipients:
        async_to_sync(channel_layer.group_send)(
            f"user.{user_id}",
            {"type": event_type, "payload": payload},
        )


def _assert_can_send(user, conversation_id):
    try:
        membership = Membership.objects.select_related("conversation").get(
            conversation_id=conversation_id,
            utilisateur=user,
        )
    except Membership.DoesNotExist as exc:
        raise PermissionDenied("Vous n’êtes pas membre de cette conversation.") from exc
    if (
        membership.conversation.type == Conversation.Type.GROUPE
        and membership.conversation.envoi_messages == Conversation.EnvoiMessages.ADMINS
        and membership.role != Membership.Role.ADMIN
    ):
        raise PermissionDenied("Seuls les administrateurs peuvent envoyer des messages.")
    return membership


def _create_receipts(message, recipient_ids):
    MessageReceipt.objects.bulk_create(
        [MessageReceipt(message=message, utilisateur_id=user_id) for user_id in recipient_ids],
        ignore_conflicts=True,
    )


def _validate_payload(message_type, contenu, media_url, duree):
    if message_type not in Message.Type.values:
        raise ValidationError("Type de message invalide.")
    if message_type == Message.Type.TEXTE and not (contenu or "").strip():
        raise ValidationError("Un message texte ne peut pas être vide.")
    if message_type != Message.Type.TEXTE and not media_url:
        raise ValidationError("Une référence média est obligatoire.")
    if duree is not None and duree <= 0:
        raise ValidationError("La durée doit être positive.")
    if message_type == Message.Type.NOTE_VOCALE and not duree:
        raise ValidationError("La durée de la note vocale est obligatoire.")


@transaction.atomic
def send_message(
    *,
    sender,
    conversation_id,
    message_type,
    contenu=None,
    media_url=None,
    media_asset_id=None,
    duree=None,
    client_id=None,
):
    enforce_rate_limit("message-user", sender.id, limit=120, period_seconds=60)
    _assert_can_send(sender, conversation_id)
    if message_type not in Message.Type.values:
        raise ValidationError("Type de message invalide.")
    contenu = normalize_message_text(contenu)
    if client_id and not isinstance(client_id, uuid.UUID):
        try:
            client_id = uuid.UUID(str(client_id))
        except (TypeError, ValueError, AttributeError) as exc:
            raise ValidationError("client_id doit être un UUID valide.") from exc

    if message_type != Message.Type.TEXTE:
        from media.models import MediaAsset
        from media.storage import object_reference

        expected_asset_type = {
            Message.Type.IMAGE: MediaAsset.Type.IMAGE,
            Message.Type.VIDEO: MediaAsset.Type.VIDEO,
            Message.Type.NOTE_VOCALE: MediaAsset.Type.NOTE_VOCALE,
        }.get(message_type)
        try:
            asset = MediaAsset.objects.get(
                pk=media_asset_id,
                conversation_id=conversation_id,
                type=expected_asset_type,
                statut=MediaAsset.Status.PRET,
            )
        except MediaAsset.DoesNotExist as exc:
            raise ValidationError("Le média n’est pas prêt ou ne correspond pas à la conversation.") from exc
        media_url = object_reference(asset.output_object_key or asset.source_object_key)
        if duree is None:
            duree = asset.duree

    _validate_payload(message_type, contenu, media_url, duree)

    message_values = {
        "type": message_type,
        "contenu": contenu or None,
        "media_url": media_url,
        "duree": duree,
    }
    if client_id:
        message, created = Message.objects.get_or_create(
            conversation_id=conversation_id,
            utilisateur_expediteur=sender,
            client_id=client_id,
            defaults=message_values,
        )
        if not created:
            return message, False
    else:
        message = Message.objects.create(
            conversation_id=conversation_id,
            utilisateur_expediteur=sender,
            **message_values,
        )
    recipient_ids = [
        user_id
        for user_id in MembershipCache.get_user_ids(conversation_id)
        if user_id != sender.id
    ]
    _create_receipts(message, recipient_ids)
    payload = message_event_payload(message)

    def publish():
        _publish_persistent_event(conversation_id, "chat.message", payload)
        notify_offline_recipients_task.delay(message.id)

    transaction.on_commit(publish)
    return message, True


@transaction.atomic
def update_receipt(*, user, message_id, status):
    ranks = {
        MessageReceipt.Status.ENVOYE: 0,
        MessageReceipt.Status.RECU: 1,
        MessageReceipt.Status.LU: 2,
    }
    if status not in ranks:
        raise ValidationError("Statut de message invalide.")
    try:
        receipt = MessageReceipt.objects.select_for_update().select_related("message").get(
            message_id=message_id,
            utilisateur=user,
        )
    except MessageReceipt.DoesNotExist as exc:
        raise PermissionDenied("Accusé de réception inaccessible.") from exc
    if ranks[status] > ranks[receipt.statut]:
        receipt.statut = status
        receipt.date_maj = timezone.now()
        receipt.save(update_fields=["statut", "date_maj"])

    payload = {
        "message_id": receipt.message_id,
        "conversation_id": receipt.message.conversation_id,
        "user_id": user.id,
        "status": receipt.statut,
        "date_maj": receipt.date_maj.isoformat(),
    }

    def publish():
        _publish_persistent_event(
            receipt.message.conversation_id,
            "chat.receipt",
            payload,
        )

    transaction.on_commit(publish)
    return receipt


def _owned_message_for_update(user, message_id):
    try:
        message = Message.objects.select_for_update().select_related("conversation").get(
            pk=message_id,
            utilisateur_expediteur=user,
        )
    except Message.DoesNotExist as exc:
        raise PermissionDenied("Message inaccessible.") from exc
    if not Membership.objects.filter(conversation=message.conversation, utilisateur=user).exists():
        raise PermissionDenied("Message inaccessible.")
    return message


@transaction.atomic
def edit_message(*, user, message_id, contenu):
    message = _owned_message_for_update(user, message_id)
    if message.type != Message.Type.TEXTE:
        raise ValidationError("Seuls les messages texte peuvent être modifiés.")
    if message.supprime_pour_tous_le:
        raise ValidationError("Un message supprimé ne peut pas être modifié.")
    contenu = normalize_message_text(contenu)
    if not contenu:
        raise ValidationError("Un message texte ne peut pas être vide.")
    message.contenu = contenu
    message.modifie_le = timezone.now()
    message.save(update_fields=["contenu", "modifie_le"])
    payload = message_event_payload(message)
    transaction.on_commit(
        lambda: _publish_persistent_event(
            message.conversation_id,
            "chat.message_updated",
            payload,
        )
    )
    return message


@transaction.atomic
def delete_message(*, user, message_id, mode):
    if mode not in {"me", "everyone"}:
        raise ValidationError("Mode de suppression invalide.")
    message = _owned_message_for_update(user, message_id)
    if mode == "me":
        MessageHiddenFor.objects.get_or_create(message=message, utilisateur=user)
        payload = {
            "message_id": message.id,
            "conversation_id": message.conversation_id,
            "user_id": user.id,
        }

        def publish_hidden():
            async_to_sync(get_channel_layer().group_send)(
                f"user.{user.id}",
                {"type": "chat.message_hidden", "payload": payload},
            )

        transaction.on_commit(publish_hidden)
        return message

    deadline = message.date_envoi + timedelta(
        hours=settings.MESSAGE_DELETE_FOR_EVERYONE_HOURS
    )
    if timezone.now() > deadline:
        raise PermissionDenied(
            f"La suppression pour tout le monde est limitée à {settings.MESSAGE_DELETE_FOR_EVERYONE_HOURS} heures."
        )
    if not message.supprime_pour_tous_le:
        message.supprime_pour_tous_le = timezone.now()
        message.save(update_fields=["supprime_pour_tous_le"])
    payload = message_event_payload(message)
    transaction.on_commit(
        lambda: _publish_persistent_event(
            message.conversation_id,
            "chat.message_deleted",
            payload,
        )
    )
    return message


@transaction.atomic
def forward_message(*, user, message_id, conversation_ids):
    try:
        source = Message.objects.select_related("conversation").get(pk=message_id)
    except Message.DoesNotExist as exc:
        raise PermissionDenied("Message inaccessible.") from exc
    if source.supprime_pour_tous_le or not Membership.objects.filter(
        conversation=source.conversation,
        utilisateur=user,
    ).exists():
        raise PermissionDenied("Message inaccessible.")
    target_ids = list(dict.fromkeys(conversation_ids))
    if not target_ids or len(target_ids) > 20:
        raise ValidationError("Sélectionnez entre 1 et 20 conversations.")

    created_messages = []
    for conversation_id in target_ids:
        _assert_can_send(user, conversation_id)
        message = Message.objects.create(
            conversation_id=conversation_id,
            utilisateur_expediteur=user,
            type=source.type,
            contenu=source.contenu,
            media_url=source.media_url,
            duree=source.duree,
            conversation_origine_id=(
                source.conversation_origine_id or source.conversation_id
            ),
        )
        recipients = [
            member_id
            for member_id in MembershipCache.get_user_ids(conversation_id)
            if member_id != user.id
        ]
        _create_receipts(message, recipients)
        created_messages.append(message)

    payloads = [(message, message_event_payload(message)) for message in created_messages]

    def publish_forwarded():
        for message, payload in payloads:
            _publish_persistent_event(message.conversation_id, "chat.message", payload)
            notify_offline_recipients_task.delay(message.id)

    transaction.on_commit(publish_forwarded)
    return created_messages


ALLOWED_REACTIONS = {"👍", "❤️", "😂", "😮", "😢", "🙏"}


@transaction.atomic
def set_message_reaction(*, user, message_id, emoji=None):
    try:
        message = Message.objects.select_for_update().get(pk=message_id)
    except Message.DoesNotExist as exc:
        raise PermissionDenied("Message inaccessible.") from exc
    if message.supprime_pour_tous_le or not Membership.objects.filter(
        conversation_id=message.conversation_id,
        utilisateur=user,
    ).exists():
        raise PermissionDenied("Message inaccessible.")
    existing = MessageReaction.objects.filter(message=message, utilisateur=user).first()
    if emoji is None or (existing and existing.emoji == emoji):
        if existing:
            existing.delete()
    else:
        if emoji not in ALLOWED_REACTIONS:
            raise ValidationError("Réaction emoji non autorisée.")
        MessageReaction.objects.update_or_create(
            message=message,
            utilisateur=user,
            defaults={"emoji": emoji},
        )
    payload = message_event_payload(message)
    transaction.on_commit(
        lambda: _publish_persistent_event(
            message.conversation_id,
            "chat.reaction",
            payload,
        )
    )
    return message
