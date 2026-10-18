from decimal import Decimal
from typing import Any

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import Avg, F, Max, Min, OuterRef, QuerySet, Subquery, Sum
from django.db.models.functions import Abs

from crypto.models import Balance, CoinPrice, Portfolio, Snapshot, WatchlistItem
from crypto.providers.base import BaseProvider
from crypto.providers.entities import Coin
from crypto.providers.provider_factory import get_provider

CACHE_TTL = 70 * 60
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


def _compute_market_stats() -> dict[str, Decimal]:
    snapshot = _get_latest_snapshot_helper()

    stats = CoinPrice.objects.filter(snapshot=snapshot).aggregate(
        min_price=Min("price"), max_price=Max("price"), avg_price=Avg("price"), total_market_cap=Sum("market_cap")
    )

    if stats["min_price"] is None:
        raise ValueError("No market data found")
    return stats


def analytics_market_stats() -> dict[str, Decimal]:
    """Возвращает статистику по рынку c кэшированием"""
    cached = cache.get(MARKET_STATS)
    if cached is not None:
        return cached
    data = _compute_market_stats()
    cache.set(MARKET_STATS, data, timeout=CACHE_TTL)
    return data


def _compute_top_movers() -> list[CoinPrice]:
    snapshot = _get_latest_snapshot_helper()
    coin_prices: list[CoinPrice] = list(
        CoinPrice.objects.filter(snapshot=snapshot)
        .annotate(volatility=Abs("price_change_percentage_24h"))
        .order_by("-volatility")[:10]
    )
    return coin_prices


def analytics_top_movers() -> list[CoinPrice]:
    """Возвращает до 10 монет по изменению цены за 24 часа с кэшированием"""
    cached = cache.get(TOP_MOVERS)
    if cached is not None:
        return cached
    data = _compute_top_movers()
    cache.set(TOP_MOVERS, data, timeout=CACHE_TTL)
    return data


def _compute_volume_leaders() -> list[CoinPrice]:
    snapshot = _get_latest_snapshot_helper()
    coin_prices = list(CoinPrice.objects.filter(snapshot=snapshot).order_by("-total_volume")[:10])
    return coin_prices


def analytics_volume_leaders() -> list[CoinPrice]:
    """Возвращает список до 10 монет по максимальному обьему торгов c кэшированием"""
    cached = cache.get(VOLUME_LEADERS)
    if cached is not None:
        return cached
    data = _compute_volume_leaders()
    cache.set(VOLUME_LEADERS, data, timeout=CACHE_TTL)
    return data


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
            TOP_MOVERS: _compute_top_movers(),
            MARKET_STATS: _compute_market_stats(),
            VOLUME_LEADERS: _compute_volume_leaders(),
        },
        timeout=CACHE_TTL,
    )


class PortfolioService:
    @transaction.atomic
    def buy(self, user: User, symbol: str, amount: Decimal) -> Portfolio | tuple[Portfolio, Decimal]:
        symbol = symbol.lower()
        if amount <= 0:
            raise ValueError("Amount must be positive")

        last_snapshot = _get_latest_snapshot_helper()
        coin: CoinPrice | None = CoinPrice.objects.filter(snapshot=last_snapshot, symbol=symbol).order_by("-id").first()
        if coin is None:
            raise ValueError("Coin not found")
        total_price = (coin.price * amount).quantize(Decimal("0.00000001"))

        balance: Balance = Balance.objects.select_for_update().get(user=user)
        if total_price > balance.amount:
            raise ValueError("Not enough balance")
        balance.amount -= total_price
        balance.save(update_fields=["amount"])

        position: Portfolio | None = Portfolio.objects.filter(user=user, symbol=symbol).first()
        if position is None:
            return Portfolio.objects.create(user=user, symbol=symbol, amount=amount, buy_price=coin.price)

        new_amount = position.amount + amount
        position.buy_price = (position.amount * position.buy_price + total_price) / new_amount
        position.amount = new_amount
        position.save(update_fields=["amount", "buy_price"])
        return position, total_price

    @transaction.atomic
    def sell(self, user: User, symbol: str, amount: Decimal) -> Balance:
        symbol = symbol.lower()
        if amount <= 0:
            raise ValueError("Amount must be positive")

        balance: Balance = Balance.objects.select_for_update().get(user=user)
        position: Portfolio | None = Portfolio.objects.filter(user=user, symbol=symbol).first()
        if position is None:
            raise ValueError("Position not found in portfolio")
        if amount > position.amount:
            raise ValueError("Not enough amount in portfolio")

        # Аварийная проверка на удаление снимка из админки
        coin: CoinPrice | None = CoinPrice.objects.filter(symbol=symbol).order_by("-id").first()
        if coin is None:
            raise ValueError("Coin not found in database")

        position.amount -= amount
        if position.amount == 0:
            position.delete()
        else:
            position.save(update_fields=["amount"])

        total_sell_price = (coin.price * amount).quantize(Decimal("0.00000001"))
        balance.amount += total_sell_price

        balance.save(update_fields=["amount"])
        return balance

    def list_positions(self, user: User) -> QuerySet[Portfolio]:
        snapshot = _get_latest_snapshot_helper()
        price_sub = (
            CoinPrice.objects.filter(snapshot=snapshot, symbol=OuterRef("symbol")).values("price").order_by("-id")[:1]
        )

        portfolio_with_curr_price = Portfolio.objects.filter(user=user).annotate(current_price=Subquery(price_sub))

        return portfolio_with_curr_price

    def get_summary(self, user: User) -> dict[str, Any]:
        snapshot = _get_latest_snapshot_helper()
        prices_sub = (
            CoinPrice.objects.filter(snapshot=snapshot, symbol=OuterRef("symbol")).values("price").order_by("-id")[:1]
        )

        positions = list(
            Portfolio.objects.filter(user=user)
            .annotate(current_price=Subquery(prices_sub))
            .annotate(
                current_value=F("amount") * F("current_price"),
                profit=F("amount") * (F("current_price") - F("buy_price")),
            )
        )

        analytics = {
            "total_value": sum((pos.current_value for pos in positions), Decimal("0")),
            "total_profit": sum((pos.profit for pos in positions), Decimal("0")),
            "positions": positions,
        }

        return analytics
