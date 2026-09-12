from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.db.models import Q
from django.utils import timezone

from .managers import UserManager
from .normalization import normalize_email, normalize_phone


class User(AbstractBaseUser, PermissionsMixin):
    class Statut(models.TextChoices):
        ACTIF = "actif", "Actif"
        INACTIF = "inactif", "Inactif"
        SUSPENDU = "suspendu", "Suspendu"

    password = models.CharField(max_length=128, db_column="mot_de_passe_hash")
    telephone = models.CharField(max_length=32, null=True, blank=True, unique=True)
    email = models.EmailField(max_length=254, null=True, blank=True, unique=True)
    nom_affichage = models.CharField(max_length=150)
    statut_personnalise = models.CharField(max_length=80, blank=True, default="Disponible sur Kozons")
    avatar_url = models.URLField(max_length=2048, null=True, blank=True)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.INACTIF)
    last_login = models.DateTimeField(null=True, blank=True, db_column="derniere_connexion")
    en_ligne = models.BooleanField(default=False)
    date_creation = models.DateTimeField(default=timezone.now, editable=False)
    tokens_valid_after = models.DateTimeField(null=True, blank=True)
    token_version = models.PositiveBigIntegerField(default=0)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nom_affichage"]

    class Meta:
        db_table = "utilisateur"
        constraints = [
            models.CheckConstraint(
                condition=(Q(telephone__isnull=False) & ~Q(telephone=""))
                | (Q(email__isnull=False) & ~Q(email="")),
                name="utilisateur_contact_requis",
            ),
            models.CheckConstraint(
                condition=Q(statut__in=["actif", "inactif", "suspendu"]),
                name="utilisateur_statut_valide",
            ),
        ]

    def save(self, *args, **kwargs):
        self.email = normalize_email(self.email)
        self.telephone = normalize_phone(self.telephone)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nom_affichage


class OTPVerification(models.Model):
    class Channel(models.TextChoices):
        SMS = "sms", "SMS"
        EMAIL = "email", "Email"

    class Purpose(models.TextChoices):
        REGISTRATION = "registration", "Inscription"
        LOGIN = "login", "Connexion"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otps")
    channel = models.CharField(max_length=8, choices=Channel.choices)
    purpose = models.CharField(max_length=16, choices=Purpose.choices)
    code_hash = models.CharField(max_length=128)
    attempts = models.PositiveSmallIntegerField(default=0)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "otp_verification"
        indexes = [
            models.Index(
                fields=["user", "purpose", "-created_at"],
                name="otp_user_purpose_created_idx",
            )
        ]

    @property
    def is_usable(self):
        return self.consumed_at is None and self.expires_at > timezone.now()


class SecurityAuditEvent(models.Model):
    actor = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="security_events"
    )
    event = models.CharField(max_length=64)
    success = models.BooleanField(default=True)
    ip_hash = models.CharField(max_length=64, blank=True)
    subject_hash = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "security_audit_event"
        indexes = [models.Index(fields=["event", "-created_at"], name="security_event_date_idx")]
