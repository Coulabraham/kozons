import uuid

import pytest

from conversations.models import Membership
from conversations.services import create_conversation
from messaging.models import Message, MessageReceipt
from messaging.services import send_message, update_receipt
from rest_framework.exceptions import ValidationError
from users.models import User


@pytest.mark.django_db(transaction=True)
def test_send_message_is_idempotent_and_creates_recipient_receipt():
    sender = User.objects.create_user(
        telephone="+221771111111",
        password="MotDePasseSolide!42",
        nom_affichage="Expéditeur",
        is_active=True,
        statut="actif",
    )
    recipient = User.objects.create_user(
        telephone="+221772222222",
        password="MotDePasseSolide!42",
        nom_affichage="Destinataire",
        is_active=True,
        statut="actif",
    )
    conversation, _ = create_conversation(
        creator=sender,
        type="individuel",
        participant_ids=[recipient.id],
    )
    client_id = uuid.uuid4()

    first, created = send_message(
        sender=sender,
        conversation_id=conversation.id,
        message_type="texte",
        contenu="Bonjour !",
        client_id=client_id,
    )
    duplicate, duplicate_created = send_message(
        sender=sender,
        conversation_id=conversation.id,
        message_type="texte",
        contenu="Bonjour !",
        client_id=client_id,
    )

    assert created is True
    assert duplicate_created is False
    assert duplicate.id == first.id
    assert Message.objects.count() == 1
    receipt = MessageReceipt.objects.get(message=first, utilisateur=recipient)
    assert receipt.statut == "envoye"

    update_receipt(user=recipient, message_id=first.id, status="lu")
    receipt.refresh_from_db()
    assert receipt.statut == "lu"
    assert Membership.objects.filter(conversation=conversation).count() == 2

    with pytest.raises(ValidationError):
        send_message(
            sender=sender,
            conversation_id=conversation.id,
            message_type="texte",
            contenu="texte\x00interdit",
        )


@pytest.mark.django_db(transaction=True)
def test_html_is_stored_as_text_not_interpreted_server_side():
    sender = User.objects.create_user(email="sender@example.test", password="MotDePasseSolide!42", nom_affichage="Sender", is_active=True, statut="actif")
    recipient = User.objects.create_user(email="recipient@example.test", password="MotDePasseSolide!42", nom_affichage="Recipient", is_active=True, statut="actif")
    conversation, _ = create_conversation(creator=sender, type="individuel", participant_ids=[recipient.id])
    payload = '<img src=x onerror="alert(1)">'
    message, _ = send_message(sender=sender, conversation_id=conversation.id, message_type="texte", contenu=payload)
    assert message.contenu == payload
