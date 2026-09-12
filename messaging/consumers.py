from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from rest_framework.exceptions import APIException

from conversations.models import Membership
from users.models import User

from .presence import PresenceService
from .services import delete_message, edit_message, send_message, set_message_reaction, update_receipt


@database_sync_to_async
def _is_member(user_id, conversation_id):
    return Membership.objects.filter(
        utilisateur_id=user_id,
        conversation_id=conversation_id,
    ).exists()


@database_sync_to_async
def _set_presence_snapshot(user_id, online):
    User.objects.filter(pk=user_id).update(en_ligne=online)


class ConversationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.group_name = f"conversation.{self.conversation_id}"
        self.connection_id = self.channel_name
        if not self.user.is_authenticated or not await _is_member(
            self.user.id, self.conversation_id
        ):
            await self.close(code=4403)
            return
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept(subprotocol=self.scope.get("accepted_subprotocol"))
        await sync_to_async(PresenceService.heartbeat)(self.user.id, self.connection_id)
        await _set_presence_snapshot(self.user.id, True)
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "presence.changed",
                "payload": {"user_id": self.user.id, "online": True},
            },
        )

    async def disconnect(self, close_code):
        if not getattr(self, "user", None) or not self.user.is_authenticated:
            return
        online = await sync_to_async(PresenceService.disconnect)(
            self.user.id, self.connection_id
        )
        if not online:
            await _set_presence_snapshot(self.user.id, False)
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "presence.changed",
                "payload": {"user_id": self.user.id, "online": online},
            },
        )
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if not await self._authorized():
            await self.close(code=4403)
            return
        event = content.get("event")
        try:
            if event == "message.send":
                await database_sync_to_async(send_message)(
                    sender=self.user,
                    conversation_id=self.conversation_id,
                    message_type=content.get("message_type"),
                    contenu=content.get("contenu"),
                    media_asset_id=content.get("media_asset_id"),
                    duree=content.get("duree"),
                    client_id=content.get("client_id"),
                )
            elif event == "receipt.update":
                await database_sync_to_async(update_receipt)(
                    user=self.user,
                    message_id=content.get("message_id"),
                    status=content.get("status"),
                )
            elif event == "message.edit":
                await database_sync_to_async(edit_message)(
                    user=self.user,
                    message_id=content.get("message_id"),
                    contenu=content.get("contenu"),
                )
            elif event == "message.delete":
                await database_sync_to_async(delete_message)(
                    user=self.user,
                    message_id=content.get("message_id"),
                    mode=content.get("mode"),
                )
            elif event == "reaction.set":
                await database_sync_to_async(set_message_reaction)(
                    user=self.user,
                    message_id=content.get("message_id"),
                    emoji=content.get("emoji"),
                )
            elif event == "typing":
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "typing.changed",
                        "payload": {
                            "user_id": self.user.id,
                            "is_typing": bool(content.get("is_typing")),
                        },
                    },
                )
            elif event == "presence.heartbeat":
                await sync_to_async(PresenceService.heartbeat)(
                    self.user.id, self.connection_id
                )
                await self.send_json({"event": "presence.heartbeat.ack"})
            else:
                await self._error("unknown_event", "Événement non pris en charge.")
        except (APIException, ValueError, TypeError) as exc:
            await self._error("invalid_event", str(exc))

    async def chat_message(self, event):
        if await self._authorized():
            await self.send_json({"event": "message.new", "data": event["payload"]})

    async def chat_receipt(self, event):
        if await self._authorized():
            await self.send_json({"event": "receipt.updated", "data": event["payload"]})

    async def chat_message_updated(self, event):
        if await self._authorized():
            await self.send_json({"event": "message.updated", "data": event["payload"]})

    async def chat_message_deleted(self, event):
        if await self._authorized():
            await self.send_json({"event": "message.deleted", "data": event["payload"]})

    async def chat_message_hidden(self, event):
        await self.send_json({"event": "message.hidden", "data": event["payload"]})

    async def chat_reaction(self, event):
        if await self._authorized():
            await self.send_json({"event": "reaction.updated", "data": event["payload"]})

    async def conversation_changed(self, event):
        await self.send_json({"event": "conversation.changed", "data": event["payload"]})

    async def typing_changed(self, event):
        if await self._authorized() and event["payload"]["user_id"] != self.user.id:
            await self.send_json({"event": "typing.changed", "data": event["payload"]})

    async def presence_changed(self, event):
        if await self._authorized():
            await self.send_json({"event": "presence.changed", "data": event["payload"]})

    async def _authorized(self):
        if await _is_member(self.user.id, self.conversation_id):
            return True
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        return False

    async def _error(self, code, detail):
        await self.send_json({"event": "error", "error": {"code": code, "detail": detail}})


class UserConsumer(AsyncJsonWebsocketConsumer):
    """Flux persistant par utilisateur, partagé par toutes ses sessions actives."""

    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close(code=4401)
            return
        self.group_name = f"user.{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept(subprotocol=self.scope.get("accepted_subprotocol"))

    async def disconnect(self, close_code):
        if getattr(self, "group_name", None):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def chat_message(self, event):
        await self.send_json({"event": "message.new", "data": event["payload"]})

    async def chat_receipt(self, event):
        await self.send_json({"event": "receipt.updated", "data": event["payload"]})

    async def chat_message_updated(self, event):
        await self.send_json({"event": "message.updated", "data": event["payload"]})

    async def chat_message_deleted(self, event):
        await self.send_json({"event": "message.deleted", "data": event["payload"]})

    async def chat_message_hidden(self, event):
        await self.send_json({"event": "message.hidden", "data": event["payload"]})

    async def chat_reaction(self, event):
        await self.send_json({"event": "reaction.updated", "data": event["payload"]})

    async def conversation_changed(self, event):
        await self.send_json({"event": "conversation.changed", "data": event["payload"]})
