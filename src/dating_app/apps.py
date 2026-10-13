from django.apps import AppConfig

class DatingAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dating_app'
    verbose_name = 'Платформа Знакомств'  # Красивое отображение в админ-панели

    def ready(self):
        # ⚠️ КРИТИЧЕСКИ ВАЖНО: Импортируем сигналы при старте приложения.
        # Без этой строчки файлы фотографий не будут удаляться с жесткого диска.
        import dating_app.signals
