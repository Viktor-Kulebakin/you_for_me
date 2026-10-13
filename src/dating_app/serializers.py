from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, ProfilePhoto, Action, DateInvitation

class RegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации по Email"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['email', 'password']

    def validate_email(self, value):
        # БЕЗОПАСНОСТЬ: Строго проверяем уникальность именно по полю email
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже зарегистрирован.")
        return value

    def create(self, validated_data):
        # Используем email в качестве username, чтобы авторизация шла через него
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class PhotoSerializer(serializers.ModelSerializer):
    """Сериализатор для Фотогалереи"""
    class Meta:
        model = ProfilePhoto
        fields = ['id', 'image', 'is_main', 'uploaded_at']


class ProfileSerializer(serializers.ModelSerializer):
    """Основной сериализатор Профиля / Анкеты"""
    email = serializers.EmailField(source='user.email', read_only=True)
    photos = PhotoSerializer(many=True, read_only=True)
    
    # Оптимизация: беремlikes_count из аннотации во вьюсете, если она есть.
    # Если аннотации нет (например, при детальном GET запросе), откатываемся на @property из модели.
    likes_count = serializers.SerializerMethodField()
    main_photo = serializers.ReadOnlyField(source='main_photo_url')

    class Meta:
        model = Profile
        fields = [
            'id', 'email', 'first_name', 'gender', 'age', 'city', 
            'interests', 'status', 'is_private', 'likes_count', 'main_photo', 'photos'
        ]

    def get_likes_count(self, obj):
        # Если во ViewSet вызван .annotate(likes_count=Count('received_actions')), Django запишет его в атрибут.
        # Это спасет от N+1 при массовом выводе анкет.
        return getattr(obj, 'likes_count', obj.likes_count)


class ActionSerializer(serializers.ModelSerializer):
    """Сериализатор для фиксации лайков / дизлайков / просмотров"""
    class Meta:
        model = Action
        fields = ['id', 'to_profile', 'action_type', 'timestamp']


class InvitationSerializer(serializers.ModelSerializer):
    """Сериализатор для приглашений на свидания"""
    class Meta:
        model = DateInvitation
        fields = ['id', 'match_user_1', 'match_user_2', 'message', 'is_accepted', 'sent_at']
