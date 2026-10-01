class ProviderError(Exception):
    """База для ошибок провайдера."""


class TemporaryProviderError(ProviderError):
    """Временный сбой (сеть, 429, 5xx), можно повторить."""


class PermanentProviderError(ProviderError):
    """Без повтора (4xx), запрос некорректен."""
