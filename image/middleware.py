from .favourites import FavoriteSessionManager
from .models import FavoriteDatabaseManager

class CustomSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated and request.session.modified:
            session_manager = FavoriteSessionManager(request)
            favorite_images = session_manager.get_favorites()
            FavoriteDatabaseManager.save_to_db(request.user, favorite_images)

        return response


