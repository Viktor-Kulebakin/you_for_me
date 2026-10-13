import os
from django.core.asgi import get_asgi_application

# 1. Устанавливаем настройки Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# 2. Инициализируем ASGI-приложение Django (строго до импорта routing!)
django_asgi_app = get_asgi_application()

# 3. Теперь импортируем Channels и ваши маршруты
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from dating_app.routing import websocket_urlpatterns

# 4. Собираем общий роутер протоколов
application = ProtocolTypeRouter({
    # Обычный HTTP трафик (REST API, админка, Swagger)
    "http": django_asgi_app,
    
    # WebSocket трафик (Чаты реального времени)
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
