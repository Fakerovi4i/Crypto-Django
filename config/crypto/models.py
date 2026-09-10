from django.db import models

class Snapshot(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=100)


class CoinPrice(models.Model):
    snapshot = models.ForeignKey(Snapshot, on_delete=models.CASCADE, related_name='coin_prices')
    coin_id = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=100)
    price = models.FloatField()
    market_cap = models.FloatField()
    total_volume = models.FloatField()
    price_change_percentage_24h = models.FloatField()
