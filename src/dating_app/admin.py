from django.contrib import admin
from django.utils.html import format_html
from .models import Profile, ProfilePhoto, Action, DateInvitation, Message


class ProfilePhotoInline(admin.TabularInline):
    """Позволяет просматривать и загружать фото прямо внутри страницы профиля"""
    model = ProfilePhoto
    extra = 1
    readonly_fields = ['preview_image']

    def preview_image(self, instance):
        if instance.image:
            return format_html('<img src="{}" style="max-height: 100px; border-radius: 5px;" />', instance.image.url)
        return "Нет фото"
    preview_image.short_description = "Предпросмотр"


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Настройка панели для Анкет пользователей"""
    list_display = ['id', 'first_name', 'gender', 'age', 'city', 'status', 'is_private', 'get_main_photo', 'created_at']
    list_filter = ['gender', 'status', 'is_private', 'city']
    search_fields = ['first_name', 'city', 'user__email']
    ordering = ['-created_at']
    inlines = [ProfilePhotoInline]  # Встраиваем фотогалерею

    def get_main_photo(self, instance):
        url = instance.main_photo_url
        if url:
            return format_html('<img src="{}" style="max-height: 40px; border-radius: 50%;" />', url)
        return "❌"
    get_main_photo.short_description = "Аватар"


@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    """Мониторинг Лайков, Дизлайков и Просмотров"""
    list_display = ['id', 'from_profile', 'to_profile', 'action_type', 'timestamp']
    list_filter = ['action_type', 'timestamp']
    search_fields = ['from_profile__first_name', 'to_profile__first_name']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Мониторинг чат-сообщений (Критические логи для модерации)"""
    list_display = ['id', 'sender', 'recipient', 'short_text', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['sender__first_name', 'recipient__first_name', 'text']

    def short_text(self, instance):
        if len(instance.text) > 50:
            return f"{instance.text[:50]}..."
        return instance.text
    short_text.short_description = "Текст сообщения"


@admin.register(DateInvitation)
class DateInvitationAdmin(admin.ModelAdmin):
    """Управление инвайтами на свидания"""
    list_display = ['id', 'match_user_1', 'match_user_2', 'is_accepted', 'sent_at']
    list_filter = ['is_accepted', 'sent_at']
