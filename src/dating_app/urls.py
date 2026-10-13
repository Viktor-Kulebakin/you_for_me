from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProfileViewSet, RegisterView

router = DefaultRouter()
router.register(r'profiles', ProfileViewSet, basename='profile')

urlpatterns = [
    # Путь для регистрации: /api/auth/register/
    path('auth/register/', RegisterView.as_view(), name='register'),
    
    # Все CRUD эндпоинты профилей, лайков и мэтчей: /api/profiles/...
    path('', include(router.urls)),
]
