import os

from django.conf import settings
from django.db.models.signals import m2m_changed, post_delete
from django.dispatch import receiver
from .models import Image

@receiver(m2m_changed, sender=Image.users_like.through)
def users_like_changed(sender, instance, **kwargs):
    """
    Сохраняем количество лайков
    """
    instance.total_likes = instance.users_like.count()
    instance.save()


@receiver(post_delete, sender=Image)
def delete_image(sender, instance, **kwargs):
    """
    Удаляем миниатюру и оригинальное изображения
    """
    image_path = os.path.join(settings.MEDIA_ROOT, instance.image.name)
    if os.path.exists(image_path):
        os.remove(image_path)

    name, extension = os.path.splitext(image_path)
    thumbnail_path = f'{name}_thumbnail{extension}'
    if os.path.exists(thumbnail_path):
        os.remove(thumbnail_path)
