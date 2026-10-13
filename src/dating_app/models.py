import os
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

class Profile(models.Model):
    """Профиль / Анкета пользователя для знакомств"""
    GENDER_CHOICES = [
        ('male', 'Мужчина'),
        ('female', 'Женщина'),
        ('other', 'Другое'),
    ]
    STATUS_CHOICES = [
        ('searching', 'В поиске'),
        ('busy', 'Занят(а)'),
        ('talking', 'Общаюсь'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, verbose_name="Пол")
    age = models.PositiveIntegerField(
        validators=[MinValueValidator(18), MaxValueValidator(100)], 
        verbose_name="Возраст"
    )
    city = models.CharField(max_length=100, verbose_name="Город")
    interests = models.TextField(blank=True, verbose_name="Увлечения / Интересы")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='searching', verbose_name="Статус")
    is_private = models.BooleanField(default=False, verbose_name="Приватный профиль (скрыть из поиска)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    def __str__(self):
        return f"{self.first_name} ({self.age}, {self.city})"

    @property
    def likes_count(self):
        """Внимание: используйте осторожно в списках (вызывает N+1)"""
        return self.received_actions.filter(action_type='like').count()

    @property
    def main_photo_url(self):
        """Внимание: используйте осторожно в списках (вызывает N+1)"""
        main_photo = self.photos.filter(is_main=True).first()
        if main_photo:
            return main_photo.image.url
        return None


class ProfilePhoto(models.Model):
    """Фотогалерея пользователя"""
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='photos', verbose_name="Профиль")
    image = models.ImageField(upload_to='user_galleries/', verbose_name="Фотография")
    is_main = models.BooleanField(default=False, verbose_name="Главная фотография анкеты")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Фотография"
        verbose_name_plural = "Фотогалерея"

    def save(self, *args, **kwargs):
        if self.is_main:
            ProfilePhoto.objects.filter(profile=self.profile, is_main=True).update(is_main=False)
        super().save(*args, **kwargs)


class Action(models.Model):
    """Система взаимодействий: История просмотров, Лайки и Дизлайки"""
    ACTION_TYPES = [
        ('view', 'Просмотр анкеты'),
        ('like', 'Лайк 👍'),
        ('dislike', 'Дизлайк 👎'),
    ]

    from_profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='sent_actions', verbose_name="Кто совершил action")
    to_profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='received_actions', verbose_name="На кого направлено")
    action_type = models.CharField(max_length=10, choices=ACTION_TYPES, verbose_name="Тип взаимодействия")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Взаимодействие"
        verbose_name_plural = "Взаимодействия"
        unique_together = ('from_profile', 'to_profile', 'action_type')
        # Защита на уровне БД: from_profile не может быть равен to_profile
        constraints = [
            models.CheckConstraint(
                check=~models.Q(from_profile=models.F('to_profile')),
                name='prevent_self_action'
            )
        ]

    def clean(self):
        if self.from_profile == self.to_profile:
            raise ValidationError("Вы не можете совершать действия (лайк/просмотр) на самого себя.")


class DateInvitation(models.Model):
    """Приглашения на свидания"""
    match_user_1 = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='invitations_host')
    match_user_2 = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='invitations_guest')
    message = models.TextField(verbose_name="Сообщение с предложением или контактами")
    is_accepted = models.BooleanField(null=True, blank=True, verbose_name="Принято")
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Приглашение на свидание"
        verbose_name_plural = "Приглашения на свидания"


class Message(models.Model):
    """Модель сообщения в чате между пользователями"""
    sender = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='sent_messages', verbose_name="Отправитель")
    recipient = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='received_messages', verbose_name="Получатель")
    text = models.TextField(verbose_name="Текст сообщения")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Время отправки")

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ['timestamp']
