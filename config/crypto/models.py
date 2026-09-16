from django.db import models

class Snapshot(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата")
    source = models.CharField(max_length=100, blank=True, null=True, verbose_name="Источник")

    def __str__(self):
        return f"ID снимка: {self.pk}"

    class Meta:
        verbose_name = "Снимок рынка"
        verbose_name_plural = "Снимки рынка"

class CoinPrice(models.Model):
    coin_id = models.CharField(max_length=100, verbose_name="ID")
    name = models.CharField(max_length=100, verbose_name="Название")
    symbol = models.CharField(max_length=100, verbose_name="Обозначение")

    price = models.DecimalField(
        max_digits=20, decimal_places=8, verbose_name="Цена"
    )
    market_cap = models.DecimalField(
        max_digits=30, decimal_places=2, verbose_name="Рыночная стоимость"
    )
    total_volume = models.DecimalField(
        max_digits=30, decimal_places=2, verbose_name="Объём средств"
    )
    price_change_percentage_24h = models.DecimalField(
        max_digits=10, decimal_places=4, verbose_name="Изменение за 24 часа"
    )

    snapshot = models.ForeignKey(Snapshot, on_delete=models.CASCADE, related_name='coin_prices', verbose_name="Снимок")

    class Meta:
        verbose_name = "Крипто-монета"
        verbose_name_plural = "Крипто-монеты"