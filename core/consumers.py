"""
WebSocket consumers for real-time Direct Messaging.
"""
import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User

from .models import Conversation, DirectMessage


class ChatConsumer(AsyncWebsocketConsumer):
    """Real-time chat for a single conversation room."""

    async def connect(self):
        self.convo_id = self.scope["url_route"]["kwargs"]["convo_id"]
        self.room_group_name = f"chat_{self.convo_id}"

        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return

        # Verify user is a participant
        is_participant = await self.is_participant(user, self.convo_id)
        if not is_participant:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        content = data.get("content", "").strip()
        if not content:
            return

        user = self.scope["user"]
        msg = await self.save_message(user, self.convo_id, content)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message_id": msg["id"],
                "content": msg["content"],
                "sender": msg["sender"],
                "sender_avatar": msg["sender_avatar"],
                "created_at": msg["created_at"],
            },
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def is_participant(self, user, convo_id):
        return Conversation.objects.filter(pk=convo_id, participants=user).exists()

    @database_sync_to_async
    def save_message(self, user, convo_id, content):
        convo = Conversation.objects.get(pk=convo_id)
        msg = DirectMessage.objects.create(
            conversation=convo,
            sender=user,
            content=content,
        )
        convo.save(update_fields=["updated_at"])
        try:
            avatar_url = user.profile.profile_picture.url
        except Exception:
            avatar_url = "/media/defaults/default_avatar.png"
        return {
            "id": msg.pk,
            "content": msg.content,
            "sender": user.username,
            "sender_avatar": avatar_url,
            "created_at": msg.created_at.isoformat(),
        }
