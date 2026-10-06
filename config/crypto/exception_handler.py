import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)

# Какой код соответствует какому HTTP-статусу
ERROR_CODES = {
    status.HTTP_400_BAD_REQUEST: "bad_request",
    status.HTTP_401_UNAUTHORIZED: "not_authenticated",
    status.HTTP_403_FORBIDDEN: "permission_denied",
    status.HTTP_404_NOT_FOUND: "not_found",
    status.HTTP_405_METHOD_NOT_ALLOWED: "method_not_allowed",
    status.HTTP_429_TOO_MANY_REQUESTS: "throttled",
}


def _to_text(data):
    """Превращает словарь или список ошибок в одну строку."""
    if isinstance(data, dict):
        return "; ".join(f"{key}: {' '.join(value)}" for key, value in data.items())
    if isinstance(data, list):
        return " ".join(data)
    return str(data)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        logger.error("Не обработанная ошибка", exc_info=exc)
        return Response(
            {"error": "Internal server error", "code": "server_error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    data = response.data
    message = data["detail"] if isinstance(data, dict) and "detail" in data else data
    response.data = {
        "error": _to_text(message),
        "code": ERROR_CODES.get(response.status_code, "error"),
    }
    return response
