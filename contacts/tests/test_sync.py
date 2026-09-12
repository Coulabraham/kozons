import pytest
from rest_framework.test import APIClient

from contacts.models import Contact
from users.models import User


@pytest.mark.django_db
def test_sync_returns_registered_users_and_creates_directional_contacts():
    owner = User.objects.create_user(
        telephone="+221771111111",
        password="MotDePasseSolide!42",
        nom_affichage="Propriétaire",
        is_active=True,
        statut="actif",
    )
    registered = User.objects.create_user(
        telephone="+221772222222",
        password="MotDePasseSolide!42",
        nom_affichage="Contact inscrit",
        is_active=True,
        statut="actif",
    )
    client = APIClient()
    client.force_authenticate(owner)

    response = client.post(
        "/api/contacts/sync/",
        {"telephones": ["+221 77 222 22 22", "+221773333333", owner.telephone]},
        format="json",
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.data["registered_contacts"]] == [registered.id]
    assert "telephone" not in response.data["registered_contacts"][0]
    assert "email" not in response.data["registered_contacts"][0]
    assert Contact.objects.filter(
        utilisateur_proprietaire=owner,
        utilisateur_contact=registered,
    ).exists()
    assert not Contact.objects.filter(utilisateur_proprietaire=registered).exists()
