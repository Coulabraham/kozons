from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIClient

from contacts.models import Contact
from conversations.models import Membership
from conversations.services import create_conversation
from messaging.models import Message, MessageHiddenFor, MessageReaction
from messaging.selectors import messages_for_user
from messaging.services import (
    delete_message,
    edit_message,
    forward_message,
    send_message,
    set_message_reaction,
)
from users.models import User


def make_user(email, name):
    return User.objects.create_user(
        email=email,
        password="MotDePasseSolide!42",
        nom_affichage=name,
        is_active=True,
        statut="actif",
    )


@pytest.mark.django_db(transaction=True)
def test_edit_hide_delete_forward_and_react_to_message():
    sender = make_user("sender-advanced@example.test", "Awa")
    recipient = make_user("recipient-advanced@example.test", "Moussa")
    third = make_user("third-advanced@example.test", "Fatou")
    source_conversation, _ = create_conversation(
        creator=sender, type="individuel", participant_ids=[recipient.id]
    )
    target_conversation, _ = create_conversation(
        creator=sender, type="individuel", participant_ids=[third.id]
    )
    message, _ = send_message(
        sender=sender,
        conversation_id=source_conversation.id,
        message_type="texte",
        contenu="Message à retrouver",
    )

    edited = edit_message(user=sender, message_id=message.id, contenu="Message modifié")
    assert edited.contenu == "Message modifié"
    assert edited.modifie_le is not None

    set_message_reaction(user=recipient, message_id=message.id, emoji="👍")
    assert MessageReaction.objects.get(message=message, utilisateur=recipient).emoji == "👍"
    set_message_reaction(user=recipient, message_id=message.id, emoji="❤️")
    assert MessageReaction.objects.get(message=message, utilisateur=recipient).emoji == "❤️"
    set_message_reaction(user=recipient, message_id=message.id, emoji="❤️")
    assert not MessageReaction.objects.filter(message=message, utilisateur=recipient).exists()

    copies = forward_message(
        user=sender,
        message_id=message.id,
        conversation_ids=[target_conversation.id],
    )
    assert len(copies) == 1
    assert copies[0].conversation_origine_id == source_conversation.id
    assert copies[0].contenu == "Message modifié"

    delete_message(user=sender, message_id=message.id, mode="me")
    assert MessageHiddenFor.objects.filter(message=message, utilisateur=sender).exists()
    assert message not in messages_for_user(user=sender, conversation_id=source_conversation.id)
    assert message in messages_for_user(user=recipient, conversation_id=source_conversation.id)

    delete_message(user=sender, message_id=message.id, mode="everyone")
    message.refresh_from_db()
    assert message.supprime_pour_tous_le is not None


@pytest.mark.django_db(transaction=True)
def test_delete_for_everyone_is_refused_after_deadline():
    sender = make_user("sender-old@example.test", "Ancien")
    recipient = make_user("recipient-old@example.test", "Destinataire")
    conversation, _ = create_conversation(
        creator=sender, type="individuel", participant_ids=[recipient.id]
    )
    message, _ = send_message(
        sender=sender, conversation_id=conversation.id, message_type="texte", contenu="Trop ancien"
    )
    Message.objects.filter(pk=message.pk).update(date_envoi=timezone.now() - timedelta(hours=49))
    with pytest.raises(PermissionDenied):
        delete_message(user=sender, message_id=message.id, mode="everyone")


@pytest.mark.django_db(transaction=True)
def test_search_endpoints_find_messages_conversations_and_contacts():
    owner = make_user("owner-search@example.test", "Propriétaire")
    peer = make_user("peer-search@example.test", "Moussa Diallo")
    contact = make_user("contact-search@example.test", "Fatou Ndiaye")
    conversation, _ = create_conversation(
        creator=owner, type="groupe", participant_ids=[peer.id], nom="Équipe Kozons"
    )
    Contact.objects.create(utilisateur_proprietaire=owner, utilisateur_contact=contact)
    send_message(
        sender=owner,
        conversation_id=conversation.id,
        message_type="texte",
        contenu="La réunion Kozons commence demain",
    )
    client = APIClient()
    client.force_authenticate(owner)

    messages = client.get(f"/api/conversations/{conversation.id}/messages/search/?q=réunion")
    assert messages.status_code == 200
    assert len(messages.data) == 1
    global_results = client.get("/api/conversations/search/?q=Kozons")
    assert global_results.status_code == 200
    assert global_results.data["conversations"][0]["id"] == conversation.id
    contacts = client.get("/api/conversations/search/?q=Fatou")
    assert contacts.data["contacts"][0]["id"] == contact.id


@pytest.mark.django_db(transaction=True)
def test_group_admin_permissions_and_admin_only_sending():
    admin = make_user("admin-group@example.test", "Admin")
    member = make_user("member-group@example.test", "Membre")
    other = make_user("other-group@example.test", "Autre")
    conversation, _ = create_conversation(
        creator=admin,
        type="groupe",
        participant_ids=[member.id, other.id],
        nom="Groupe initial",
    )
    admin_client = APIClient()
    admin_client.force_authenticate(admin)
    member_client = APIClient()
    member_client.force_authenticate(member)

    forbidden = member_client.patch(
        f"/api/conversations/{conversation.id}/",
        {"nom": "Interdit"},
        format="json",
    )
    assert forbidden.status_code == 403
    updated = admin_client.patch(
        f"/api/conversations/{conversation.id}/",
        {"nom": "Groupe sécurisé", "envoi_messages": "admins"},
        format="json",
    )
    assert updated.status_code == 200
    assert updated.data["envoi_messages"] == "admins"

    denied_message = member_client.post(
        f"/api/conversations/{conversation.id}/messages/",
        {"type": "texte", "contenu": "Je ne devrais pas passer"},
        format="json",
    )
    assert denied_message.status_code == 403
    promoted = admin_client.patch(
        f"/api/conversations/{conversation.id}/members/{member.id}/role/",
        {"role": "admin"},
        format="json",
    )
    assert promoted.status_code == 200
    assert Membership.objects.get(conversation=conversation, utilisateur=member).role == "admin"
    removed = admin_client.delete(
        f"/api/conversations/{conversation.id}/members/{other.id}/"
    )
    assert removed.status_code == 204
    assert not Membership.objects.filter(conversation=conversation, utilisateur=other).exists()
