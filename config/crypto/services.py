from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import Min, Max, Avg, Sum, QuerySet
from django.db.models.functions import Abs

from crypto.models import WatchlistItem, Snapshot, CoinPrice
from crypto.providers.base import BaseProvider
from crypto.providers.provider_factory import get_provider


def watchlist_item_add(*, symbol: str, user: User) -> QuerySet:
    """
    Добавляет symbol в watchlist
    """
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


def watchlist_items_list(*, user: User) -> QuerySet:
    return WatchlistItem.objects.filter(user=user)


def watchlist_item_delete(*, user: User, item_id: int) -> None:
    try:
        item_id = int(item_id)
    except (ValueError, TypeError):
        raise ValueError(f"Item {item_id} not found")

    try:
        item = WatchlistItem.objects.get(user=user, id=item_id)
    except WatchlistItem.DoesNotExist:
        raise ValueError(f"Item {item_id} not found")
    item.delete()


def _get_latest_snapshot_helper() -> Snapshot:
    latest_snapshot = Snapshot.objects.first()  # ordering -created_at
    if latest_snapshot is None:
        raise ValueError("No snapshots found")
    return latest_snapshot


def analytics_market_stats() -> dict:
    snapshot = _get_latest_snapshot_helper()

    stats = CoinPrice.objects.filter(snapshot=snapshot).aggregate(
        min_price=Min('price'),
        max_price=Max('price'),
        avg_price=Avg('price'),
        total_market_cap=Sum('market_cap')
    )

    if stats['min_price'] is None:
        raise ValueError("No market data found")

    return stats


def analytics_top_movers():
    snapshot = _get_latest_snapshot_helper()

    coin_prices = CoinPrice.objects.filter(
        snapshot=snapshot
    ).annotate(volatility=Abs(
        'price_change_percentage_24h')
    ).order_by('-volatility')[:10]

    return coin_prices


def analytics_volume_leaders():
    snapshot = _get_latest_snapshot_helper()

    coin_prices = CoinPrice.objects.filter(
        snapshot=snapshot
    ).order_by('-total_volume')[:10]

    return coin_prices



