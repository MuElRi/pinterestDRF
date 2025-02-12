import os
from django.contrib.auth.signals import user_logged_in
from .models import FavoriteDatabaseManager
from .favourites import FavoriteSessionManager
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


@receiver(user_logged_in)
def merge_favorites_on_login(sender, request, user, **kwargs):
    # Получаем избранное из сессии
    session_manager = FavoriteSessionManager(request)
    favorites = set(session_manager.get_favorites())  # Избранное из сессии

    if favorites:  # Если в сессии есть избранные
        db_favorites = set(FavoriteDatabaseManager.load_from_db(user))
        merged_favorites = favorites | db_favorites  # Объединяем множества
        session_manager.save_favorites(merged_favorites)
        FavoriteDatabaseManager.save_to_db(user, merged_favorites)  # Записываем в БД


