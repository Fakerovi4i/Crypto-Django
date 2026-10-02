import functools

import redis
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response


def handle_not_found(method):
    """Декоратор для обработки не найденных данных"""

    def warpper(self, request, *args, **kwargs):
        try:
            return method(self, request, *args, **kwargs)
        except ValueError as e:
            return Response(data={"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

    return warpper


_redis_client = redis.from_url(settings.CELERY_RESULT_BACKEND)


def single_instance(key: str, ttl: int = 1800):
    """Гарантирует, что задача выполняется только в одном экземпляре."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            lock_key = f"lock:{key}"
            # nx - не позволит перезаписать ключ и вернут None
            if not _redis_client.set(lock_key, "locked", nx=True, ex=ttl):
                return {"skipped": True}

            try:
                return func(*args, **kwargs)
            finally:
                _redis_client.delete(lock_key)

        return wrapper

    return decorator
