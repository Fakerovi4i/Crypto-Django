from decimal import Decimal

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models


class Snapshot(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата")
    source = models.CharField(max_length=100, blank=True, default="", verbose_name="Источник")

    def __str__(self):
        return f"ID снимка: {self.pk}"

    class Meta:
        verbose_name = "Снимок рынка"
        verbose_name_plural = "Снимки рынка"
        ordering = ["-created_at"]


class CoinPrice(models.Model):
    coin_id = models.CharField(max_length=100, verbose_name="ID")
    name = models.CharField(max_length=100, verbose_name="Название")
    symbol = models.CharField(max_length=100, verbose_name="Обозначение")

    price = models.DecimalField(max_digits=20, decimal_places=8, verbose_name="Цена")
    market_cap = models.DecimalField(max_digits=30, decimal_places=2, verbose_name="Рыночная стоимость")
    total_volume = models.DecimalField(max_digits=30, decimal_places=2, verbose_name="Объём средств")
    price_change_percentage_24h = models.DecimalField(
        max_digits=10, decimal_places=4, verbose_name="Изменение за 24 часа"
    )

    snapshot = models.ForeignKey(Snapshot, on_delete=models.CASCADE, related_name="coin_prices", verbose_name="Снимок")

    class Meta:
        verbose_name = "Крипто-монета"
        verbose_name_plural = "Крипто-монеты"
        indexes = [
            models.Index(fields=["snapshot", "symbol"], name="idx_coinprice_snapshot_symbol"),
        ]


class WatchlistItem(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="watchlist_items", verbose_name="Пользователь"
    )
    coin_symbol = models.CharField(max_length=50, verbose_name="Монета")

    class Meta:
        verbose_name = "Coin hystory"
        verbose_name_plural = "Монеты отслеживания"
        ordering = ["coin_symbol"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "coin_symbol"],
                name="unique_user_coin_symbol",
            )
        ]

    def __str__(self):
        return f"{self.user} — {self.coin_symbol}"


class Balance(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="balance",
        verbose_name="Пользователь",
    )

    amount = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        verbose_name="Баланс в USD",
        default=0,
        validators=[MinValueValidator(Decimal("0"))],
    )

    class Meta:
        verbose_name = "Balance"
        verbose_name_plural = "Кошельки"

        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gte=0),
                name="balance_amount_non_negative",
            ),
        ]

    def __str__(self):
        return f"{self.user} -- {self.amount}"


class Portfolio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="portfolios", verbose_name="Пользователь")
    symbol = models.CharField(max_length=50, verbose_name="Обозначение")
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        verbose_name="Количество",
        validators=[MinValueValidator(Decimal("0"))],
    )
    buy_price = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        verbose_name="Цена покупки",
    )
    bought_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата покупки")

    class Meta:
        verbose_name = "Позиция портфеля"
        verbose_name_plural = "Позиции портфеля"
        ordering = ["-bought_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "symbol"],
                name="unique_user_symbol_portfolio",
            ),
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="portfolio_amount_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(buy_price__gt=0),
                name="portfolio_buy_price_positive",
            ),
        ]

    def __str__(self):
        return f"{self.user} -- {self.amount} -- {self.symbol} -- {self.buy_price}"
