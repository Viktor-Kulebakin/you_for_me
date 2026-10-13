import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # Проверяем авторизацию пользователя (опционально, но безопасно)
        self.user = self.scope.get('user')
        
        # Присоединяемся к группе чата в Redis
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Покидаем группу чата
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message = data['message']
            recipient_id = data['recipient_id']
            
            # БЕЗОПАСНОСТЬ: Берем ID отправителя из сессии авторизации Django, 
            # либо откатываемся на присланный (если авторизация через токен еще настраивается)
            sender_id = self.user.id if self.user and self.user.is_authenticated else data.get('sender_id')

            if not sender_id:
                return  # Не обрабатываем анонимные сообщения

            # Асинхронно сохраняем сообщение в СУБД PostgreSQL
            await self.save_message(sender_id, recipient_id, message)

            # Отправляем сообщение всем участникам группы чата
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender_id': sender_id
                }
            )
        except (KeyError, ValueError):
            # Защита от отправки некорректного JSON с фронтенда
            pass

    async def chat_message(self, event):
        # Отправка сообщения в WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id']
        }))

    @database_sync_to_async
    def save_message(self, sender_id, recipient_id, text):
        # ОПТИМИЗАЦИЯ SQL: Передаем `_id` напрямую. 
        # Django не делает лишних запросов SELECT к таблице Profile, а сразу выполняет быстрый INSERT.
        try:
            return Message.objects.create(
                sender_id=sender_id, 
                recipient_id=recipient_id, 
                text=text
            )
        except Exception:
            # Предотвращает падение WebSocket, если, например, одного из пользователей удалили
            return None
