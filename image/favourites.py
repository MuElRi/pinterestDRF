from django.conf import settings

from image.models import FavoriteDatabaseManager


class FavoriteSessionManager:

    def __init__(self, request):
        self.session = request.session
        self.user = request.user

    def get_favorites(self):
        """Получаем список избранных изображений из сессии.
        Если в сессии нет избранных, смотрим в БД (для авторизованных пользователей)"""
        favorites = self.session.get(settings.FAVORITE_SESSION_ID, [])
        if not favorites:
            if self.user.is_authenticated:
                favorites = FavoriteDatabaseManager.load_from_db(self.user)

        return favorites

    def add_favorite(self, image_id):
        """Добавляем изображение в избранное"""
        favorites = self.get_favorites()
        if image_id not in favorites:
            favorites.append(image_id)
            self.session["favorite_images"] = favorites
            self._save()

    def save_favorites(self, favorites):
        self.session['favorite_images'] = list(favorites)

    def remove_favorite(self, image_id):
        """Удаляем изображение из избранного"""
        favorites = self.get_favorites()
        if image_id in favorites:
            favorites.remove(image_id)
            if not favorites:
                del self.session["favorite_images"]
            else:
                self.session["favorite_images"] = favorites
            self._save()

    def _save(self):
        self.session.modified = True