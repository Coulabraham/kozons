from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class Contact(models.Model):
    utilisateur_proprietaire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="contacts_possedes",
        db_column="id_utilisateur_proprietaire",
    )
    utilisateur_contact = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="present_dans_les_contacts",
        db_column="id_utilisateur_contact",
    )
    date_ajout = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "contact"
        constraints = [
            models.UniqueConstraint(
                fields=["utilisateur_proprietaire", "utilisateur_contact"],
                name="contact_proprietaire_contact_uniq",
            ),
            models.CheckConstraint(
                condition=~Q(utilisateur_proprietaire=F("utilisateur_contact")),
                name="contact_pas_soi_meme",
            ),
        ]
