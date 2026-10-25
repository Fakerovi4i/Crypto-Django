import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone

from crypto.models import CoinPrice, Snapshot


class Command(BaseCommand):
    help = "Наполняет БД тестовыми снимками и ценами монет"

    def add_arguments(self, parser):
        parser.add_argument("--snapshots", type=int, default=500)
        parser.add_argument("--coins", type=int, default=100)

    def handle(self, *args, **options):
        n_snapshots, n_coins = options["snapshots"], options["coins"]
        rng = random.Random(42)  # фиксированное зерно: каждый запуск даёт одинаковые данные

        # 100 монет: цена и "количество в обращении" задаются один раз
        coins = [
            {
                "coin_id": f"coin-{i}",
                "name": f"Coin {i}",
                "symbol": f"c{i}",
                "price": rng.uniform(0.01, 60000),
                "supply": rng.uniform(1e6, 1e9),
            }
            for i in range(n_coins)
        ]

        with transaction.atomic():
            # source="seed" позволит потом удалить тестовые данные одним запросом
            snapshots = Snapshot.objects.bulk_create([Snapshot(source="seed") for _ in range(n_snapshots)])

            # auto_now_add выставил "сейчас", растягиваем снимки по времени с шагом 10 минут (как Beat)
            start = timezone.now() - timedelta(minutes=10 * n_snapshots)
            for i, snap in enumerate(snapshots):
                snap.created_at = start + timedelta(minutes=10 * i)
            Snapshot.objects.bulk_update(snapshots, ["created_at"])

            prices = []
            for snap in snapshots:
                for coin in coins:
                    coin["price"] *= 1 + rng.gauss(0, 0.01)  # цена "блуждает" на ~1%
                    market_cap = coin["price"] * coin["supply"]
                    prices.append(
                        CoinPrice(
                            snapshot=snap,
                            coin_id=coin["coin_id"],
                            name=coin["name"],
                            symbol=coin["symbol"],
                            price=round(coin["price"], 8),
                            market_cap=round(market_cap, 2),
                            total_volume=round(market_cap * rng.uniform(0.01, 0.2), 2),
                            price_change_percentage_24h=round(rng.uniform(-10, 10), 4),
                        )
                    )
            CoinPrice.objects.bulk_create(prices, batch_size=5000)

        # Обновляем статистику планировщика, иначе EXPLAIN покажет план по устаревшим данным
        with connection.cursor() as cursor:
            cursor.execute(f"ANALYZE {Snapshot._meta.db_table}")
            cursor.execute(f"ANALYZE {CoinPrice._meta.db_table}")

        self.stdout.write(self.style.SUCCESS(f"Создано снимков: {n_snapshots}, строк CoinPrice: {len(prices)}"))
