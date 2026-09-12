import pytest
from asgiref.sync import async_to_sync
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator

from conversations.services import create_conversation
from conversations.models import Membership
from messaging.middleware import JWTAuthMiddleware
from messaging.models import Message
from messaging.routing import websocket_urlpatterns
from messaging.services import send_message, update_receipt
from users.models import User
from users.tokens import issue_refresh_token


@pytest.mark.django_db(transaction=True)
def test_authenticated_member_can_send_message_over_websocket():
    sender = User.objects.create_user(
        telephone="+221771111111",
        password="MotDePasseSolide!42",
        nom_affichage="Expéditeur WebSocket",
        is_active=True,
        statut="actif",
    )
    recipient = User.objects.create_user(
        telephone="+221772222222",
        password="MotDePasseSolide!42",
        nom_affichage="Destinataire WebSocket",
        is_active=True,
        statut="actif",
    )
    conversation, _ = create_conversation(
        creator=sender,
        type="individuel",
        participant_ids=[recipient.id],
    )
    token = str(issue_refresh_token(sender).access_token)
    application = JWTAuthMiddleware(URLRouter(websocket_urlpatterns))

    async def scenario():
        communicator = WebsocketCommunicator(
            application,
            f"/ws/conversations/{conversation.id}/?token={token}",
        )
        connected, _ = await communicator.connect()
        assert connected
        presence = await communicator.receive_json_from(timeout=2)
        assert presence["event"] == "presence.changed"

        await communicator.send_json_to(
            {
                "event": "message.send",
                "client_id": "f9af129e-a39d-4fc0-9e48-939ecf64a827",
                "message_type": "texte",
                "contenu": "Message temps réel",
            }
        )
        event = await communicator.receive_json_from(timeout=2)
        assert event["event"] == "message.new"
        assert event["data"]["contenu"] == "Message temps réel"
        await communicator.disconnect()

    async_to_sync(scenario)()
    assert Message.objects.filter(conversation=conversation, contenu="Message temps réel").exists()


@pytest.mark.django_db(transaction=True)
def test_membership_is_rechecked_for_each_websocket_event():
    sender = User.objects.create_user(email="ws@example.test", password="MotDePasseSolide!42", nom_affichage="WS", is_active=True, statut="actif")
    recipient = User.objects.create_user(email="peer@example.test", password="MotDePasseSolide!42", nom_affichage="Peer", is_active=True, statut="actif")
    conversation, _ = create_conversation(creator=sender, type="individuel", participant_ids=[recipient.id])
    token = str(issue_refresh_token(sender).access_token)
    application = JWTAuthMiddleware(URLRouter(websocket_urlpatterns))

    async def scenario():
        communicator = WebsocketCommunicator(application, f"/ws/conversations/{conversation.id}/", subprotocols=["kozons", f"kozons.jwt.{token}"])
        connected, protocol = await communicator.connect()
        assert connected and protocol == "kozons"
        await communicator.receive_json_from(timeout=2)
        await database_sync_to_async(Membership.objects.filter(conversation=conversation, utilisateur=sender).delete)()
        await communicator.send_json_to({"event": "typing", "is_typing": True})
        output = await communicator.receive_output(timeout=2)
        assert output["type"] == "websocket.close"
        assert output["code"] == 4403

    from channels.db import database_sync_to_async
    async_to_sync(scenario)()


@pytest.mark.django_db(transaction=True)
def test_user_events_reach_all_active_devices():
    sender = User.objects.create_user(email="multi-sender@example.test", password="MotDePasseSolide!42", nom_affichage="Multi", is_active=True, statut="actif")
    recipient = User.objects.create_user(email="multi-recipient@example.test", password="MotDePasseSolide!42", nom_affichage="Recipient", is_active=True, statut="actif")
    conversation, _ = create_conversation(creator=sender, type="individuel", participant_ids=[recipient.id])
    sender_token = str(issue_refresh_token(sender).access_token)
    recipient_token = str(issue_refresh_token(recipient).access_token)
    application = JWTAuthMiddleware(URLRouter(websocket_urlpatterns))

    async def scenario():
        device_one = WebsocketCommunicator(application, f"/ws/users/me/?token={sender_token}")
        device_two = WebsocketCommunicator(application, f"/ws/users/me/?token={sender_token}")
        recipient_device = WebsocketCommunicator(application, f"/ws/users/me/?token={recipient_token}")
        assert (await device_one.connect())[0]
        assert (await device_two.connect())[0]
        assert (await recipient_device.connect())[0]

        message, _ = await database_sync_to_async(send_message)(
            sender=sender,
            conversation_id=conversation.id,
            message_type="texte",
            contenu="Synchronisé sur tous les appareils",
        )
        first = await device_one.receive_json_from(timeout=2)
        second = await device_two.receive_json_from(timeout=2)
        received = await recipient_device.receive_json_from(timeout=2)
        assert first["event"] == second["event"] == received["event"] == "message.new"
        assert first["data"]["id"] == second["data"]["id"] == message.id

        await database_sync_to_async(update_receipt)(
            user=recipient,
            message_id=message.id,
            status="lu",
        )
        receipt_one = await device_one.receive_json_from(timeout=2)
        receipt_two = await device_two.receive_json_from(timeout=2)
        assert receipt_one["event"] == receipt_two["event"] == "receipt.updated"
        assert receipt_one["data"]["status"] == "lu"

        await device_one.disconnect()
        await device_two.disconnect()
        await recipient_device.disconnect()

    from channels.db import database_sync_to_async
    async_to_sync(scenario)()
