from celery.result import AsyncResult
from django.core.cache import cache
import redis
from django.conf import settings


def task_exists(task_id):
    """Проверяет, есть ли запись о задаче в Redis backend."""
    r = redis.from_url(settings.CELERY_RESULT_BACKEND)
    key = f"celery-task-meta-{task_id}"
    return r.exists(key) == 1