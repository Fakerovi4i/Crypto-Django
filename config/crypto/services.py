from decimal import Decimal
from typing import Any

import structlog
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import DatabaseError, IntegrityError, connection, transaction
from django.db.models import Avg, F, Max, Min, OuterRef, QuerySet, Subquery, Sum
from django.db.models.functions import Abs
from prometheus_client import Counter

from config.celery import app as celery_app
from crypto.models import Balance, CoinPrice, Portfolio, Snapshot, WatchlistItem
from crypto.providers.base import BaseProvider
from crypto.providers.entities import Coin
from crypto.providers.provider_factory import get_provider

logger = structlog.get_logger(__name__)


CACHE_TTL = 70 * 60
TOP_MOVERS = "top_movers"
MARKET_STATS = "market_stats"
VOLUME_LEADERS = "volume_leaders"

CACHE_LOOKUPS = Counter("crypto_cache_total", "Cache lookups", labelnames=["key_prefix", "result"])


def _cache_get(key: str) -> Any | None:
    result = cache.get(key)
    CACHE_LOOKUPS.labels(key_prefix=key, result="hit" if result is not None else "miss").inc()
    return result


def watchlist_item_add(*, symbol: str, user: User) -> WatchlistItem:
    """Добавляет symbol в watchlist"""

    symbol = symbol.lower()
    provider: BaseProvider = get_provider()
    with provider as p:
        if not p.symbol_exists(symbol):
            logger.warning(
                "validate_symbol", user_id=user.pk, symbol=symbol, provider=settings.EXCHANGE_PROVIDER, status="error"
            )
            raise ValueError("Symbol not found")
        logger.info(
            "validate_symbol", user_id=user.pk, symbol=symbol, provider=settings.EXCHANGE_PROVIDER, status="success"
        )

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
    cached = _cache_get(MARKET_STATS)
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
    cached = _cache_get(TOP_MOVERS)
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
    cached = _cache_get(VOLUME_LEADERS)
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


def _get_latest_coin_price(symbol: str) -> CoinPrice:
    last_snapshot = _get_latest_snapshot_helper()
    coin = CoinPrice.objects.filter(snapshot=last_snapshot, symbol=symbol).order_by("-id").first()
    if coin is None:
        raise ValueError("Coin not found")
    return coin


class PortfolioService:
    @transaction.atomic
    def buy(self, user: User, symbol: str, amount: Decimal) -> tuple[Portfolio, Decimal]:
        symbol = symbol.lower()
        if amount <= 0:
            raise ValueError("Amount must be positive")
        coin = _get_latest_coin_price(symbol)
        total_price = (coin.price * amount).quantize(Decimal("0.00000001"))

        balance: Balance = Balance.objects.select_for_update().get(user=user)
        if total_price > balance.amount:
            logger.warning(
                "buy_coin",
                user_id=user.pk,
                symbol=symbol,
                amount=str(amount),
                total_price=str(total_price),
                balance=str(balance.amount),
                status="error",
            )
            raise ValueError("Not enough balance")
        balance.amount -= total_price
        balance.save(update_fields=["amount"])

        position: Portfolio | None = Portfolio.objects.filter(user=user, symbol=symbol).first()
        if position is None:
            position = Portfolio.objects.create(user=user, symbol=symbol, amount=amount, buy_price=coin.price)
        else:
            new_amount = position.amount + amount
            position.buy_price = (position.amount * position.buy_price + total_price) / new_amount
            position.amount = new_amount
            position.save(update_fields=["amount", "buy_price"])
        logger.info(
            "buy_coin",
            user_id=user.pk,
            symbol=symbol,
            amount=str(amount),
            total_price=str(total_price),
            balance=str(balance.amount),
            status="success",
        )
        return position, total_price

    @transaction.atomic
    def sell(self, user: User, symbol: str, amount: Decimal) -> Balance:
        symbol = symbol.lower()
        if amount <= 0:
            raise ValueError("Amount must be positive")

        balance: Balance = Balance.objects.select_for_update().get(user=user)
        position: Portfolio | None = Portfolio.objects.filter(user=user, symbol=symbol).first()
        if position is None:
            logger.warning("sell_position", user_id=user.pk, symbol=symbol, amount=str(amount))
            raise ValueError("Position not found in portfolio")
        if amount > position.amount:
            raise ValueError("Not enough amount in portfolio")

        coin = _get_latest_coin_price(symbol)

        position.amount -= amount
        if position.amount == 0:
            position.delete()
        else:
            position.save(update_fields=["amount"])

        total_sell_price = (coin.price * amount).quantize(Decimal("0.00000001"))
        balance.amount += total_sell_price

        balance.save(update_fields=["amount"])
        logger.info(
            "sell_position",
            user_id=user.pk,
            symbol=symbol,
            amount=str(amount),
            balance=str(balance.amount),
            position=position.amount,
            status="success",
        )
        return balance

    @staticmethod
    def subquery_price() -> QuerySet:
        snapshot = _get_latest_snapshot_helper()
        return (
            CoinPrice.objects.filter(snapshot=snapshot, symbol=OuterRef("symbol")).values("price").order_by("-id")[:1]
        )

    def list_positions(self, user: User) -> QuerySet[Portfolio]:
        portfolio_with_curr_price = Portfolio.objects.filter(user=user).annotate(
            current_price=Subquery(self.subquery_price())
        )

        return portfolio_with_curr_price

    def get_summary(self, user: User) -> dict[str, Any]:
        positions = list(
            Portfolio.objects.filter(user=user)
            .annotate(current_price=Subquery(self.subquery_price()))
            .annotate(
                current_value=F("amount") * F("current_price"),
                profit=F("amount") * (F("current_price") - F("buy_price")),
            )
            .filter(current_price__isnull=False)
        )

        analytics = {
            "total_value": sum((pos.current_value for pos in positions), Decimal("0")),
            "total_profit": sum((pos.profit for pos in positions), Decimal("0")),
            "positions": positions,
        }

        return analytics


def _check_db() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True
    except DatabaseError as e:
        logger.warning("health_check_failed", check="database", error=str(e))
        return False


def _check_cache() -> bool:
    try:
        cache.set("health_chech", "ok", timeout=5)
        # По ответу понимаем жив ли редис, соединение не проверить из-за IGNORE_EXCEPTIONS
        return cache.get("health_chech") == "ok"
    except Exception as e:
        logger.warning("health_check_failed", check="cache", error=str(e))
        return False


def _check_celery_broker() -> bool:
    try:
        resp = celery_app.control.ping(timeout=2.0, limit=1)
    except Exception as e:
        logger.warning("health_check_failed", check="celery", error=str(e))
        return False
    return bool(resp)


def get_helth_db_cache_celery() -> tuple[dict, bool]:
    checks = {
        "database": _check_db(),
        "cache": _check_cache(),
        "celery_broker": _check_celery_broker(),
    }
    is_ok = all(checks.values())
    response = {
        "status": "ok" if is_ok else "degraded",
        "checks": {name: "ok" if ok else "fail" for name, ok in checks.items()},
    }
    return response, is_ok
