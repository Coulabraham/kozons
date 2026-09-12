from django.conf import settings
from django.db import models
from django.utils import timezone


class PushSubscription(models.Model):
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="push_subscriptions",
        db_column="id_utilisateur",
    )
    endpoint = models.URLField(max_length=2048, unique=True)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(default=timezone.now, editable=False)
    date_maj = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "push_subscription"
        indexes = [
            models.Index(fields=["utilisateur", "actif"], name="push_user_active_idx")
        ]
