from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from conversations.models import Conversation


class MediaAsset(models.Model):
    class Type(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Vidéo"
        NOTE_VOCALE = "note_vocale", "Note vocale"

    class Status(models.TextChoices):
        EN_ATTENTE = "en_attente", "En attente d’upload"
        UPLOADE = "uploade", "Uploadé"
        TRAITEMENT = "traitement", "En traitement"
        PRET = "pret", "Prêt"
        ECHEC = "echec", "Échec"

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="medias",
        db_column="id_utilisateur",
    )
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="medias",
        null=True,
        blank=True,
        db_column="id_conversation",
    )
    type = models.CharField(max_length=12, choices=Type.choices)
    statut = models.CharField(max_length=12, choices=Status.choices, default=Status.EN_ATTENTE)
    source_object_key = models.CharField(max_length=1024, unique=True)
    output_object_key = models.CharField(max_length=1024, null=True, blank=True)
    thumbnail_object_key = models.CharField(max_length=1024, null=True, blank=True)
    content_type = models.CharField(max_length=100)
    taille_octets = models.PositiveBigIntegerField()
    duree = models.PositiveIntegerField(null=True, blank=True)
    erreur = models.TextField(null=True, blank=True)
    date_creation = models.DateTimeField(default=timezone.now, editable=False)
    date_maj = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "media_asset"
        constraints = [
            models.CheckConstraint(
                condition=Q(type__in=["image", "video", "note_vocale"]),
                name="media_type_valide",
            ),
            models.CheckConstraint(
                condition=Q(
                    statut__in=["en_attente", "uploade", "traitement", "pret", "echec"]
                ),
                name="media_statut_valide",
            ),
            models.CheckConstraint(
                condition=Q(taille_octets__gt=0),
                name="media_taille_positive",
            ),
        ]
