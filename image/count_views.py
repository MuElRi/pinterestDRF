from django.core.cache import cache

from image.admin import ImageAdmin
from image.models import Image


class CountViewsImage:

    def get_cache_key(self, image_id):
        return f"image:{image_id}:views"

    def incr(self, image_id):
        cache_key = self.get_cache_key(image_id)
        if not cache.get(cache_key):
            image = Image.objects.get(id=image_id)
            cache.set(cache_key, image.views)
        return cache.incr(cache_key)

    def get(self, image_id):
        cache_key = self.get_cache_key(image_id)
        if not cache.get(cache_key):
            image = Image.objects.get(id=image_id)
            cache.set(cache_key, image.views)
        return cache.get(cache_key)
