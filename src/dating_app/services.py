import random
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import Profile, Action, DateInvitation, Message

class DatingService:
    """Слой бизнес-логики для платформы знакомств «You for Me»"""

    @staticmethod
    def get_filtered_random_profile(user_profile: Profile, filters: dict) -> Profile:
        """
        Алгоритм умного поиска (К5 + Оптимизация).
        Исключает себя, приватных и уже оцененных. Возвращает готовый объект профиля.
        """
        # Находим ID всех оцененных профилей
        evaluated_ids = Action.objects.filter(from_profile=user_profile).values_list('to_profile_id', flat=True)
        
        # Базовый запрос
        queryset = Profile.objects.filter(is_private=False).exclude(id=user_profile.id).exclude(id__in=evaluated_ids)
        
        # Применяем фильтры динамически
        if filters.get('gender'): queryset = queryset.filter(gender=filters['gender'])
        if filters.get('city'): queryset = queryset.filter(city=filters['city'])
        if filters.get('status'): queryset = queryset.filter(status=filters['status'])
        
        # Выбираем случайный ID без просадки производительности СУБД (OFFSET)
        profile_ids = list(queryset.values_list('id', flat=True))
        if not profile_ids:
            return None
            
        random_id = random.choice(profile_ids)
        
        # Делаем один чистый запрос с предзагрузкой связей
        random_profile = Profile.objects.select_related('user').prefetch_related('photos').get(id=random_id)
        
        # Автоматически фиксируем просмотр
        Action.objects.get_or_create(from_profile=user_profile, to_profile=random_profile, action_type='view')
        return random_profile


    @staticmethod
    @transaction.atomic
    def handle_profile_action(from_profile: Profile, target_profile_id: int, action_type: str) -> dict:
        """
        Единая система оценивания анкет (К2) с защитой от дублирования.
        Возвращает статус операции и факт взаимного мэтча.
        """
        if from_profile.id == int(target_profile_id):
            raise ValidationError("Вы не можете оценивать собственный профиль.")

        target_profile = Profile.objects.get(id=target_profile_id)

        # Удаляем конфликтующие или старые действия
        Action.objects.filter(from_profile=from_profile, to_profile=target_profile).delete()
        
        # Создаем новое взаимодействие
        Action.objects.create(from_profile=from_profile, to_profile=target_profile, action_type=action_type)

        is_match = False
        if action_type == 'like':
            # Проверяем, лайкал ли этот человек нас ранее
            is_match = Action.objects.filter(from_profile=target_profile, to_profile=from_profile, action_type='like').exists()

        return {
            'success': True,
            'action_type': action_type,
            'is_match': is_match
        }


    @staticmethod
    def send_date_invitation(from_profile: Profile, to_profile_id: int, message: str) -> DateInvitation:
        """
        Бизнес-валидация инвайтов (К3): отправить инвайт на свидание можно 
        только в случае взаимного мэтча (наличия обоюдных лайков).
        """
        target_profile = Profile.objects.get(id=to_profile_id)
        
        # Проверяем взаимность лайков
        has_my_like = Action.objects.filter(from_profile=from_profile, to_profile=target_profile, action_type='like').exists()
        has_target_like = Action.objects.filter(from_profile=target_profile, to_profile=from_profile, action_type='like').exists()
        
        if not (has_my_like and has_target_like):
            raise ValidationError("Вы можете пригласить на свидание только при наличии взаимного мэтча.")

        return DateInvitation.objects.create(
            match_user_1=from_profile,
            match_user_2=target_profile,
            message=message
        )


    @staticmethod
    def save_chat_message(sender_id: int, recipient_id: int, text: str) -> Message:
        """Сохранение сообщения для WebSocket-консьюмера чата"""
        try:
            return Message.objects.create(
                sender_id=sender_id,
                recipient_id=recipient_id,
                text=text
            )
        except Exception as e:
            return None
