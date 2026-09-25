from rest_framework import status
from rest_framework.response import Response


def handle_not_found(method):
    """Декоратор для обработки не найденных данных"""
    def warpper(self, request, *args, **kwargs):
        try:
            return method(self, request, *args, **kwargs)
        except ValueError as e:
            return Response(data={'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)
    return warpper
