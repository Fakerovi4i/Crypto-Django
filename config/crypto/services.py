# TODO: Изменить тайммаут перед сдачей на 70 минут beat сделать 60 минут
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import Avg, Max, Min, QuerySet, Sum
from django.db.models.functions import Abs

from crypto.models import CoinPrice, Snapshot, WatchlistItem
from crypto.providers.base import BaseProvider
from crypto.providers.entities import Coin
from crypto.providers.provider_factory import get_provider

CACHE_TTL = 240
TOP_MOVERS = "top_movers"
MARKET_STATS = "market_stats"
VOLUME_LEADERS = "volume_leaders"


def watchlist_item_add(*, symbol: str, user: User) -> WatchlistItem:
    """Добавляет symbol в watchlist"""

    symbol = symbol.lower()
    provider: BaseProvider = get_provider()
    with provider as p:
        if not p.symbol_exists(symbol):
            raise ValueError("Symbol not found")
    try:
        item = WatchlistItem.objects.create(user=user, coin_symbol=symbol)
    except IntegrityError:
        raise ValueError("Symbol already in watchlist")
    return item


def watchlist_items_list(*, user: User) -> QuerySet[WatchlistItem]:
    return WatchlistItem.objects.filter(user=user)


def watchlist_item_delete(*, user: User, item_id: str) -> None:
    try:
        item_pk = int(item_id)
    except ValueError, TypeError:
        raise ValueError(f"Item {item_id} not found")

    try:
        item = WatchlistItem.objects.get(user=user, id=item_pk)
    except WatchlistItem.DoesNotExist:
        raise ValueError(f"Item {item_id} not found")
    item.delete()


def _get_latest_snapshot_helper() -> Snapshot:
    """Возвращает последний снапшот"""
    latest_snapshot = Snapshot.objects.first()  # ordering -created_at
    if latest_snapshot is None:
        raise ValueError("No snapshots found")
    return latest_snapshot


def analytics_market_stats() -> dict[str, Decimal]:
    """Возвращает статистику по рынку c кэшированием"""
    cached = cache.get(MARKET_STATS)
    if cached is not None:
        return cached

    snapshot = _get_latest_snapshot_helper()
    stats = CoinPrice.objects.filter(snapshot=snapshot).aggregate(
        min_price=Min("price"), max_price=Max("price"), avg_price=Avg("price"), total_market_cap=Sum("market_cap")
    )

    if stats["min_price"] is None:
        raise ValueError("No market data found")

    cache.set(MARKET_STATS, stats, timeout=CACHE_TTL)
    return stats


def analytics_top_movers() -> list[CoinPrice]:
    """Возвращает до 10 монет по изменению цены за 24 часа с кэшированием"""
    cached = cache.get(TOP_MOVERS)
    if cached is not None:
        return cached

    snapshot = _get_latest_snapshot_helper()

    coin_prices: list[CoinPrice] = list(
        CoinPrice.objects.filter(snapshot=snapshot)
        .annotate(volatility=Abs("price_change_percentage_24h"))
        .order_by("-volatility")[:10]
    )

    cache.set(TOP_MOVERS, coin_prices, timeout=CACHE_TTL)
    return coin_prices


def analytics_volume_leaders() -> list[CoinPrice]:
    """Возвращает список до 10 монет по максимальному обьему торгов c кэшированием"""
    cached = cache.get(VOLUME_LEADERS)
    if cached is not None:
        return cached

    snapshot = _get_latest_snapshot_helper()
    coin_prices = list(CoinPrice.objects.filter(snapshot=snapshot).order_by("-total_volume")[:10])

    cache.set(VOLUME_LEADERS, coin_prices, timeout=CACHE_TTL)
    return coin_prices


def fetch_and_save_snapshot() -> Snapshot:
    provider: BaseProvider = get_provider()

    with provider as p:
        coins: list[Coin] = p.get_coins()

    with transaction.atomic():
        snapshot = Snapshot.objects.create(source=settings.EXCHANGE_PROVIDER)
        CoinPrice.objects.bulk_create(
            [
                CoinPrice(
                    coin_id=c.id,
                    name=c.name,
                    symbol=c.symbol,
                    price=c.price,
                    market_cap=c.market_cap,
                    total_volume=c.total_volume,
                    price_change_percentage_24h=c.price_change_percentage_24h,
                    snapshot=snapshot,
                )
                for c in coins
            ]
        )

    return snapshot


def analytics_cache() -> None:
    """Кэширует данные для аналитики"""
    cache.set_many(
        {
            TOP_MOVERS: list(analytics_top_movers()),
            MARKET_STATS: analytics_market_stats(),
            VOLUME_LEADERS: analytics_volume_leaders(),
        },
        timeout=CACHE_TTL,
    )
