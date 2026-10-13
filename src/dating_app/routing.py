from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Маршрут для подключения к чат-комнате по её ID
    # ВНИМАНИЕ: Заменили .as_view() на .as_asgi()
    re_path(r'ws/chat/(?P<room_name>\d+)/$', consumers.ChatConsumer.as_asgi()),
]
