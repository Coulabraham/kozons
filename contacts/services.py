from django.db import transaction

from users.models import User
from users.normalization import normalize_phone

from .models import Contact


@transaction.atomic
def synchronize_contacts(*, owner, phone_numbers):
    if len(phone_numbers) > 1000:
        raise ValueError("La synchronisation est limitée à 1 000 numéros par requête.")
    normalized = []
    seen = set()
    for value in phone_numbers:
        phone = normalize_phone(value)
        if phone and phone not in seen:
            normalized.append(phone)
            seen.add(phone)

    users = list(
        User.objects.filter(telephone__in=normalized, is_active=True)
        .exclude(pk=owner.pk)
        .only("id", "telephone", "email", "nom_affichage", "avatar_url", "statut", "date_creation")
    )
    Contact.objects.bulk_create(
        [
            Contact(utilisateur_proprietaire=owner, utilisateur_contact=user)
            for user in users
        ],
        ignore_conflicts=True,
    )
    order = {phone: index for index, phone in enumerate(normalized)}
    users.sort(key=lambda user: order[user.telephone])
    return users
