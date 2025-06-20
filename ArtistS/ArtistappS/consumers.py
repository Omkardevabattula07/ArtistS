import json
import base64
import os
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from .models import Room, Message
from django.core.files.base import ContentFile
from asgiref.sync import sync_to_async
from django.utils import timezone

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message', '')
        file_data = data.get('file', '')
        filename = data.get('filename', '')

        user = self.scope['user']
        room = await sync_to_async(Room.objects.get)(name=self.room_name)

        if file_data and filename:
            format, file_str = file_data.split(';base64,')
            ext = filename.split('.')[-1]
            file_content = ContentFile(base64.b64decode(file_str), name=filename)

            msg = Message(
                room=room,
                sender=user,
                file=file_content,
                file_extension=ext,
                timestamp=timezone.now()
            )
            await sync_to_async(msg.save)()

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': '',
                    'sender': user.username,
                    'file_url': msg.file.url,
                    'file_ext': ext,
                    'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                }
            )
        elif message:
            msg = Message(
                room=room,
                sender=user,
                content=message,
                timestamp=timezone.now()
            )
            await sync_to_async(msg.save)()

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender': user.username,
                    'file_url': '',
                    'file_ext': '',
                    'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                }
            )

    # Receive message from room group
    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))
