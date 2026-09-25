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
                name='Coin_2',
                symbol='coin_2',
                price=1000,
                market_cap=1000000,
                total_volume=1000000,
                price_change_percentage_24h=10,
                snapshot=snapshot_2
            )
            CoinPrice.objects.create(
                coin_id=str(i),
                name='Coin_3',
                symbol='coin_3',
                price=500,
                market_cap=1000000,
                total_volume=1000000,
                price_change_percentage_24h=10,
                snapshot=snapshot_2
            )
            CoinPrice.objects.create(
                coin_id=str(i),
                name='Coin_4',
                symbol='coin_4',
                price=1500,
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


    def test_coin_price_history_filter_symbol(self):
        """Проверяет фильтрацию истории цены"""
        response = self.client.get('/api/coins/?symbol=coin_2')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 5) # всего в фильтре
        self.assertEqual(len(response.data['results']), 5)  # на странице


    def test_coin_price_history_filter_min_max_price(self):
        response = self.client.get('/api/coins/?min_price=500&max_price=1500')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 15)  # всего в фильтре
        self.assertEqual(len(response.data['results']), 10)  # на странице, пагинация по 10


    def test_coin_price_history_filter_min_max_price_edge_case(self):
        response = self.client.get('/api/coins/?min_price=501&max_price=1499')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 5)  # всего в фильтре






