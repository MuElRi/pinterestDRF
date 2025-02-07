import redis
from django.conf import settings

r = redis.Redis(host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB)

class CountViewsImage:

    def  get_redis_key(self, image_id):
        return f"image:{image_id}:views"

    def incr(self, image_id):
        redis_key = self.get_redis_key(image_id)
        return r.incr(redis_key)

    def get(self, image_id):
        redis_key = self.get_redis_key(image_id)
        return r.get(redis_key) or 0
