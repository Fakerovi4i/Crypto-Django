from rest_framework import status
from rest_framework.test import APITestCase

from crypto.models import CoinPrice, Snapshot


class CoinsApiTests(APITestCase):
    def setUp(self):
        snapshot_1 = Snapshot.objects.create()
        snapshot_2 = Snapshot.objects.create()

        for i in range(5):
            CoinPrice.objects.create(
                coin_id=str(i),
                name='Coin_1',
                symbol='coin_1',
                price=100,
                market_cap=1000000,
                total_volume=1000000,
                price_change_percentage_24h=10,
                snapshot=snapshot_1
            )
            CoinPrice.objects.create(
                coin_id=str(i),
                name='Coin_1',
                symbol='coin_1',
                price=100,
                market_cap=1000000,
                total_volume=1000000,
                price_change_percentage_24h=10,
                snapshot=snapshot_2
            )

    def test_coin_price_history_count_sql_queries(self):
        """Проверяет количество запросов при получении истории цены"""
        # Без select_related 12 запросов
        with self.assertNumQueries(2):
            response = self.client.get('/api/coins/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)


