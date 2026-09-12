import hashlib

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from users.models import User

from .cache import MembershipCache
from .models import Conversation, Membership


_UNSET = object()


def _publish_conversation_event(conversation_id, event, payload, user_ids=None):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"conversation.{conversation_id}",
        {"type": "conversation.changed", "payload": {"event": event, **payload}},
    )
    for user_id in user_ids or MembershipCache.get_user_ids(conversation_id):
        async_to_sync(channel_layer.group_send)(
            f"user.{user_id}",
            {"type": "conversation.changed", "payload": {"event": event, **payload}},
        )


def _admin_membership(*, user, conversation_id, lock=False):
    queryset = Membership.objects.select_related("conversation")
    if lock:
        queryset = queryset.select_for_update()
    try:
        membership = queryset.get(conversation_id=conversation_id, utilisateur=user)
    except Membership.DoesNotExist as exc:
        raise PermissionDenied("Conversation inaccessible.") from exc
    if membership.conversation.type != Conversation.Type.GROUPE:
        raise ValidationError("Cette action est réservée aux groupes.")
    if membership.role != Membership.Role.ADMIN:
        raise PermissionDenied("Action réservée aux administrateurs du groupe.")
    return membership


def _individual_key(user_ids):
    canonical = ":".join(str(value) for value in sorted(user_ids))
    return hashlib.sha256(canonical.encode()).hexdigest()


@transaction.atomic
def create_conversation(*, creator, type, participant_ids, nom=None, avatar_media_id=None):
    ids = set(participant_ids)
    ids.add(creator.id)
    users = list(User.objects.filter(id__in=ids, is_active=True))
    if len(users) != len(ids):
        raise ValidationError("Un ou plusieurs participants sont invalides.")
    if len(users) > 256:
        raise ValidationError("Une conversation est limitée à 256 membres.")

    if type == Conversation.Type.INDIVIDUEL:
        if len(users) != 2:
            raise ValidationError("Une conversation individuelle doit contenir deux membres.")
        key = _individual_key(ids)
        conversation, created = Conversation.objects.get_or_create(
            individual_key=key,
            defaults={"type": type, "utilisateur_createur": creator},
        )
        if not created:
            return conversation, False
    elif type == Conversation.Type.GROUPE:
        if not nom or not nom.strip():
            raise ValidationError("Le nom est obligatoire pour un groupe.")
        avatar_reference = None
        if avatar_media_id is not None:
            from media.models import MediaAsset
            from media.storage import object_reference

            try:
                avatar_asset = MediaAsset.objects.get(
                    pk=avatar_media_id,
                    utilisateur=creator,
                    conversation__isnull=True,
                    type=MediaAsset.Type.IMAGE,
                    statut=MediaAsset.Status.PRET,
                )
            except MediaAsset.DoesNotExist as exc:
                raise ValidationError("La photo du groupe n'est pas prête ou ne vous appartient pas.") from exc
            avatar_reference = object_reference(
                avatar_asset.output_object_key or avatar_asset.source_object_key
            )
        conversation = Conversation.objects.create(
            type=type,
            nom=nom.strip(),
            avatar_url=avatar_reference,
            utilisateur_createur=creator,
        )
    else:
        raise ValidationError("Type de conversation invalide.")

    Membership.objects.bulk_create(
        [
            Membership(
                conversation=conversation,
                utilisateur=user,
                role=Membership.Role.ADMIN if user.id == creator.id else Membership.Role.MEMBRE,
            )
            for user in users
        ]
    )
    MembershipCache.invalidate(conversation.id)
    return conversation, True


@transaction.atomic
def leave_conversation(*, user, conversation_id):
    try:
        membership = Membership.objects.select_for_update().select_related("conversation").get(
            conversation_id=conversation_id,
            utilisateur=user,
        )
    except Membership.DoesNotExist as exc:
        raise ValidationError("Conversation inaccessible.") from exc
    conversation = membership.conversation
    was_admin = membership.role == Membership.Role.ADMIN
    membership.delete()
    remaining = Membership.objects.filter(conversation=conversation).order_by("date_ajout", "id")
    if not remaining.exists():
        conversation.delete()
    elif was_admin and not remaining.filter(role=Membership.Role.ADMIN).exists():
        successor = remaining.first()
        successor.role = Membership.Role.ADMIN
        successor.save(update_fields=["role"])
    MembershipCache.invalidate(conversation_id)


@transaction.atomic
def update_group(*, user, conversation_id, nom=None, avatar_media_id=_UNSET, envoi_messages=None):
    membership = _admin_membership(user=user, conversation_id=conversation_id, lock=True)
    conversation = membership.conversation
    fields = []
    if nom is not None:
        if not nom.strip():
            raise ValidationError("Le nom du groupe ne peut pas être vide.")
        conversation.nom = nom.strip()
        fields.append("nom")
    if envoi_messages is not None:
        if envoi_messages not in Conversation.EnvoiMessages.values:
            raise ValidationError("Permission d’envoi invalide.")
        conversation.envoi_messages = envoi_messages
        fields.append("envoi_messages")
    if avatar_media_id is not _UNSET:
        if avatar_media_id is None:
            conversation.avatar_url = None
        else:
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
                raise ValidationError("La photo du groupe n’est pas prête ou ne vous appartient pas.") from exc
            conversation.avatar_url = object_reference(asset.output_object_key or asset.source_object_key)
        fields.append("avatar_url")
    if fields:
        conversation.save(update_fields=fields)
        transaction.on_commit(
            lambda: _publish_conversation_event(
                conversation.id,
                "conversation.updated",
                {"conversation_id": conversation.id},
            )
        )
    return conversation


@transaction.atomic
def remove_group_member(*, user, conversation_id, member_user_id):
    admin = _admin_membership(user=user, conversation_id=conversation_id, lock=True)
    recipients = MembershipCache.get_user_ids(conversation_id)
    if member_user_id == user.id:
        raise ValidationError("Utilisez l’action quitter le groupe pour vous retirer.")
    if member_user_id == admin.conversation.utilisateur_createur_id:
        raise PermissionDenied("Le créateur du groupe ne peut pas être retiré.")
    try:
        target = Membership.objects.select_for_update().get(
            conversation_id=conversation_id,
            utilisateur_id=member_user_id,
        )
    except Membership.DoesNotExist as exc:
        raise ValidationError("Ce membre n’appartient pas au groupe.") from exc
    target.delete()
    MembershipCache.invalidate(conversation_id)
    payload = {"conversation_id": conversation_id, "user_id": member_user_id}
    transaction.on_commit(
        lambda: _publish_conversation_event(
            conversation_id,
            "member.removed",
            payload,
            recipients,
        )
    )


@transaction.atomic
def set_group_member_role(*, user, conversation_id, member_user_id, role):
    _admin_membership(user=user, conversation_id=conversation_id, lock=True)
    if role not in Membership.Role.values:
        raise ValidationError("Rôle invalide.")
    try:
        target = Membership.objects.select_for_update().get(
            conversation_id=conversation_id,
            utilisateur_id=member_user_id,
        )
    except Membership.DoesNotExist as exc:
        raise ValidationError("Ce membre n’appartient pas au groupe.") from exc
    if target.role == Membership.Role.ADMIN and role == Membership.Role.MEMBRE:
        admin_count = Membership.objects.filter(
            conversation_id=conversation_id,
            role=Membership.Role.ADMIN,
        ).count()
        if admin_count <= 1:
            raise ValidationError("Un groupe doit conserver au moins un administrateur.")
    target.role = role
    target.save(update_fields=["role"])
    MembershipCache.invalidate(conversation_id)
    payload = {"conversation_id": conversation_id, "user_id": member_user_id, "role": role}
    transaction.on_commit(
        lambda: _publish_conversation_event(conversation_id, "member.role_updated", payload)
    )
    return target
