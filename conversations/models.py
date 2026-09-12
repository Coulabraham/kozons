from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Conversation(models.Model):
    class Type(models.TextChoices):
        INDIVIDUEL = "individuel", "Individuel"
        GROUPE = "groupe", "Groupe"

    class EnvoiMessages(models.TextChoices):
        TOUS = "tous", "Tous les membres"
        ADMINS = "admins", "Administrateurs uniquement"

    type = models.CharField(max_length=12, choices=Type.choices)
    nom = models.CharField(max_length=150, null=True, blank=True)
    avatar_url = models.URLField(max_length=2048, null=True, blank=True)
    utilisateur_createur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="conversations_creees",
        db_column="id_utilisateur_createur",
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="Membership",
        related_name="conversations",
    )
    individual_key = models.CharField(max_length=64, null=True, blank=True, unique=True)
    envoi_messages = models.CharField(
        max_length=8,
        choices=EnvoiMessages.choices,
        default=EnvoiMessages.TOUS,
    )
    date_creation = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "conversation"
        constraints = [
            models.CheckConstraint(
                condition=Q(type__in=["individuel", "groupe"]),
                name="conversation_type_valide",
            ),
            models.CheckConstraint(
                condition=Q(type="individuel") | (Q(nom__isnull=False) & ~Q(nom="")),
                name="conversation_groupe_nom_requis",
            ),
            models.CheckConstraint(
                condition=(Q(type="individuel") & Q(individual_key__isnull=False))
                | (Q(type="groupe") & Q(individual_key__isnull=True)),
                name="conversation_cle_individuelle_valide",
            ),
            models.CheckConstraint(
                condition=Q(envoi_messages__in=["tous", "admins"]),
                name="conversation_envoi_messages_valide",
            ),
        ]


class Membership(models.Model):
    class Role(models.TextChoices):
        ADMIN = "admin", "Administrateur"
        MEMBRE = "membre", "Membre"

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="membres",
        db_column="id_conversation",
    )
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="participations",
        db_column="id_utilisateur",
    )
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBRE)
    date_ajout = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "membre_conversation"
        constraints = [
            models.UniqueConstraint(
                fields=["conversation", "utilisateur"],
                name="membre_conversation_utilisateur_uniq",
            ),
            models.CheckConstraint(
                condition=Q(role__in=["admin", "membre"]),
                name="membre_role_valide",
            ),
        ]
