from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from conversations.models import Conversation


class Message(models.Model):
    class Type(models.TextChoices):
        TEXTE = "texte", "Texte"
        NOTE_VOCALE = "note_vocale", "Note vocale"
        IMAGE = "image", "Image"
        VIDEO = "video", "Vidéo"

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
        db_column="id_conversation",
    )
    utilisateur_expediteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="messages_envoyes",
        db_column="id_utilisateur_expediteur",
    )
    client_id = models.UUIDField(null=True, blank=True)
    type = models.CharField(max_length=12, choices=Type.choices)
    contenu = models.TextField(null=True, blank=True)
    media_url = models.CharField(max_length=2048, null=True, blank=True)
    duree = models.PositiveIntegerField(null=True, blank=True, help_text="Durée en secondes")
    date_envoi = models.DateTimeField(default=timezone.now, editable=False)
    modifie_le = models.DateTimeField(null=True, blank=True)
    supprime_pour_tous_le = models.DateTimeField(null=True, blank=True)
    conversation_origine = models.ForeignKey(
        Conversation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="messages_transferes",
        db_column="id_conversation_origine",
    )

    class Meta:
        db_table = "message"
        indexes = [
            models.Index(
                fields=["conversation", "-date_envoi", "-id"],
                name="message_conv_date_id_idx",
            )
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["conversation", "utilisateur_expediteur", "client_id"],
                condition=Q(client_id__isnull=False),
                name="message_client_id_uniq",
            ),
            models.CheckConstraint(
                condition=Q(type__in=["texte", "note_vocale", "image", "video"]),
                name="message_type_valide",
            ),
            models.CheckConstraint(
                condition=(Q(type="texte") & Q(contenu__isnull=False) & ~Q(contenu=""))
                | (
                    Q(type__in=["note_vocale", "image", "video"])
                    & Q(media_url__isnull=False)
                    & ~Q(media_url="")
                ),
                name="message_charge_utile_valide",
            ),
            models.CheckConstraint(
                condition=Q(duree__isnull=True) | Q(duree__gt=0),
                name="message_duree_positive",
            ),
            models.CheckConstraint(
                condition=~Q(type="note_vocale") | Q(duree__gt=0),
                name="message_vocal_duree_requise",
            ),
        ]


class MessageReceipt(models.Model):
    class Status(models.TextChoices):
        ENVOYE = "envoye", "Envoyé"
        RECU = "recu", "Reçu"
        LU = "lu", "Lu"

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="statuts",
        db_column="id_message",
    )
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="statuts_messages",
        db_column="id_utilisateur",
    )
    statut = models.CharField(max_length=6, choices=Status.choices, default=Status.ENVOYE)
    date_maj = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "statut_message"
        constraints = [
            models.UniqueConstraint(
                fields=["message", "utilisateur"],
                name="statut_message_utilisateur_uniq",
            ),
            models.CheckConstraint(
                condition=Q(statut__in=["envoye", "recu", "lu"]),
                name="statut_message_valide",
            ),
        ]
        indexes = [
            models.Index(
                fields=["utilisateur", "statut", "-date_maj"],
                name="statut_user_state_date_idx",
            )
        ]


class MessageHiddenFor(models.Model):
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="masquages",
        db_column="id_message",
    )
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="messages_masques",
        db_column="id_utilisateur",
    )
    date_masquage = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "message_masque_utilisateur"
        constraints = [
            models.UniqueConstraint(
                fields=["message", "utilisateur"],
                name="message_masque_utilisateur_uniq",
            )
        ]


class MessageReaction(models.Model):
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="reactions",
        db_column="id_message",
    )
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reactions_messages",
        db_column="id_utilisateur",
    )
    emoji = models.CharField(max_length=16)
    date_creation = models.DateTimeField(default=timezone.now, editable=False)
    date_maj = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reaction_message"
        constraints = [
            models.UniqueConstraint(
                fields=["message", "utilisateur"],
                name="reaction_message_utilisateur_uniq",
            )
        ]
        indexes = [
            models.Index(fields=["message", "emoji"], name="reaction_message_emoji_idx")
        ]
