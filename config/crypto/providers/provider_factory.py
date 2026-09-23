from .base import BaseProvider
from .coingecko import ProviderCoingecko
from .connector import Connector
from django.conf import settings


def get_provider() -> BaseProvider:
    """Использовать как контекстный менеджер"""
    providers = {
        'coingecko': ProviderCoingecko,
        # 'coinmarketcap': ProviderCoinMarketCap,
    }
    name_provider = settings.EXCHANGE_PROVIDER
    provider_class = providers.get(name_provider)

    if provider_class is None:
        raise ValueError(f'Unknown provider: {name_provider}')

    return provider_class(connector=Connector())