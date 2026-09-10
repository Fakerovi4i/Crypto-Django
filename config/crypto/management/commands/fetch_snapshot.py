from django.core.management.base import BaseCommand

from crypto.models import CoinPrice, Snapshot

from crypto.providers.coingecko import ProviderCoingecko
from crypto.providers.connector import Connector
from crypto.providers.entities import Coin



# from crypto.providers import ProviderCoingecko  # твой существующий класс


class Command(BaseCommand):
    help = "Запрашивает данные с API биржи и сохраняет снимок рынка в БД"

    def handle(self, *args, **options):
        with ProviderCoingecko(connector=Connector()) as provider:
            coins: list[Coin] = provider.get_coins()

        snapshot = Snapshot.objects.create(source="coingecko")

        CoinPrice.objects.bulk_create([
            CoinPrice(coin_id=c.id,
                      name=c.name,
                      symbol=c.symbol,
                      price=c.price,
                      market_cap=c.market_cap,
                      total_volume=c.total_volume,
                      price_change_percentage_24h=c.price_change_percentage_24h,
                      snapshot=snapshot
                      )
            for c in coins
        ])

        self.stdout.write(self.style.SUCCESS(f"Сохранен снимок {snapshot.pk}. Кол-во монет: {len(coins)}"))
