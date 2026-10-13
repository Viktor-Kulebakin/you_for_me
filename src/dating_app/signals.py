import os
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import ProfilePhoto

@receiver(post_delete, sender=ProfilePhoto)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """Удаляет файл фотографии с жесткого диска при удалении записи из БД"""
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)
