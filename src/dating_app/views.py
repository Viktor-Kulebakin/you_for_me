import random
from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User
from .models import Profile, ProfilePhoto, Action, DateInvitation
from .serializers import RegisterSerializer, ProfileSerializer, PhotoSerializer, InvitationSerializer

class RegisterView(generics.CreateAPIView):
    """Эндпоинт регистрации по Email"""
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer


class ProfileViewSet(viewsets.ModelViewSet):
    """CRUD API для работы с анкетами, лайками и умным поиском"""
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['gender', 'age', 'city', 'status']

    def get_queryset(self):
        # Если это запрос списка всех анкет (лента), скрываем приватные.
        # Для детальных операций (свой профиль) разрешаем видеть приватный.
        if self.action == 'list' or self.action == 'random_profile':
            return Profile.objects.filter(is_private=False).select_related('user').prefetch_related('photos')
        return Profile.objects.all().select_related('user').prefetch_related('photos')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'], url_path='random')
    def random_profile(self, request):
        """Алгоритм ТЗ: получение случайной анкеты с учетом фильтров и исключений"""
        user_profile = request.user.profile
        
        # 1. Находим ID всех профилей, с которыми пользователь уже взаимодействовал
        evaluated_profile_ids = Action.objects.filter(from_profile=user_profile).values_list('to_profile_id', flat=True)
        
        # 2. Базовый фильтр: исключаем себя, приватных и уже оцененных людей
        queryset = Profile.objects.filter(is_private=False).exclude(id=user_profile.id).exclude(id__in=evaluated_profile_ids)
        
        # 3. Применяем входящие GET-фильтры
        gender = request.query_params.get('gender')
        city = request.query_params.get('city')
        status_param = request.query_params.get('status')
        
        if gender: queryset = queryset.filter(gender=gender)
        if city: queryset = queryset.filter(city=city)
        if status_param: queryset = queryset.filter(status=status_param)
        
        # 4. ОПТИМИЗАЦИЯ СЛУЧАЙНОГО ВЫБОРА: запрашиваем только ID, чтобы не грузить БД срезами
        profile_ids = list(queryset.values_list('id', flat=True))
        if not profile_ids:
            return Response({'detail': 'Подходящие анкеты закончились!'}, status=status.HTTP_404_NOT_FOUND)
            
        random_id = random.choice(profile_ids)
        random_profile = Profile.objects.select_related('user').prefetch_related('photos').get(id=random_id)
        
        # Фиксируем автоматический 'view'
        Action.objects.get_or_create(from_profile=user_profile, to_profile=random_profile, action_type='view')
        
        serializer = self.get_serializer(random_profile)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Поставить лайк 👍 профилю"""
        user_profile = request.user.profile
        target_profile = self.get_object()
        
        action_obj, created = Action.objects.get_or_create(
            from_profile=user_profile, to_profile=target_profile, action_type='like'
        )
        Action.objects.filter(from_profile=user_profile, to_profile=target_profile, action_type='dislike').delete()

        # Проверяем на взаимность
        is_match = Action.objects.filter(from_profile=target_profile, to_profile=user_profile, action_type='like').exists()
        
        return Response({'liked': True, 'is_match': is_match}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def dislike(self, request, pk=None):
        """Поставить дизлайк 👎 профилю"""
        user_profile = request.user.profile
        target_profile = self.get_object()
        
        Action.objects.filter(from_profile=user_profile, to_profile=target_profile, action_type='like').delete()
        Action.objects.get_or_create(from_profile=user_profile, to_profile=target_profile, action_type='dislike')
        
        return Response({'disliked': True}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='matches')
    def my_matches(self, request):
        """Список взаимных лайков (Мэтчей)"""
        user_profile = request.user.profile
        my_likes = Action.objects.filter(from_profile=user_profile, action_type='like').values_list('to_profile_id', flat=True)
        mutual_likes = Action.objects.filter(from_profile_id__in=my_likes, to_profile=user_profile, action_type='like').values_list('from_profile_id', flat=True)
        
        profiles = Profile.objects.filter(id__in=mutual_likes).prefetch_related('photos')
        serializer = self.get_serializer(profiles, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='views-history')
    def views_history(self, request):
        """История просмотренных профилей (К3 + К5 оптимизация)"""
        user_profile = self.request.user.profile
        actions = Action.objects.filter(from_profile=user_profile, action_type='view').select_related('to_profile').prefetch_related('to_profile__photos')
        profiles = [a.to_profile for a in actions]
        serializer = self.get_serializer(profiles, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='liked-profiles')
    def liked_profiles(self, request):
        """Список понравившихся пользователей (Кто понравился мне)"""
        user_profile = self.request.user.profile
        actions = Action.objects.filter(from_profile=user_profile, action_type='like').select_related('to_profile').prefetch_related('to_profile__photos')
        profiles = [a.to_profile for a in actions]
        serializer = self.get_serializer(profiles, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='disliked-profiles')
    def disliked_profiles(self, request):
        """Список НЕпонравившихся пользователей (Дизлайки от меня)"""
        user_profile = self.request.user.profile
        actions = Action.objects.filter(from_profile=user_profile, action_type='dislike').select_related('to_profile').prefetch_related('to_profile__photos')
        profiles = [a.to_profile for a in actions]
        serializer = self.get_serializer(profiles, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='likes-on-me')
    def likes_on_me(self, request):
        """История лайков моего профиля (Кто лайкнул меня)"""
        user_profile = self.request.user.profile
        actions = Action.objects.filter(to_profile=user_profile, action_type='like').select_related('from_profile').prefetch_related('from_profile__photos')
        profiles = [a.from_profile for a in actions]
        serializer = self.get_serializer(profiles, many=True)
        return Response(serializer.data)
