from typing import TYPE_CHECKING

from django.core.cache import caches
from rest_framework.throttling import AnonRateThrottle as CustomAnonRateThrottle
from rest_framework.throttling import UserRateThrottle

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.views import APIView


class RegularUserRateThrottle(UserRateThrottle):
    """100/мин для авторизованных. Суперпользователей пропускает."""

    scope = "user"
    cache = caches["throttle"]

    def get_cache_key(self, request: Request, view: APIView) -> str | None:
        if request.user.is_superuser:
            return None
        return super().get_cache_key(request, view)


class AdminRateThrottle(UserRateThrottle):
    """1000/мин для суперпользователей."""

    scope = "admin"
    cache = caches["throttle"]

    def get_cache_key(self, request: Request, view: APIView) -> str | None:
        if not request.user.is_superuser:
            return None
        return super().get_cache_key(request, view)


class AnonRateThrottle(CustomAnonRateThrottle):
    scope = "anon"
    cache = caches["throttle"]
