from .base import BaseProvider
from .coingecko import ProviderCoingecko
from .connector import Connector
from django.conf import settings


def get_provider() -> BaseProvider:
    """Использовать как контекстный менеджер"""
    name_provider = settings.EXCHANGE_PROVIDER

    if name_provider == 'coingecko':
        return ProviderCoingecko(connector=Connector())

    raise ValueError(f'Unknown provider: {name_provider}')

