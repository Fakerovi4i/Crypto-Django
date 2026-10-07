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
                name="Coin_1",
                symbol="coin_1",
                price=100,
                market_cap=1000000,
                total_volume=1000000,
                price_change_percentage_24h=10,
                snapshot=snapshot_1,
            )
            CoinPrice.objects.create(
                coin_id=str(i),
                name="Coin_2",
                symbol="coin_2",
                price=1000,
                market_cap=1000000,
                total_volume=1000000,
                price_change_percentage_24h=10,
                snapshot=snapshot_2,
            )
            CoinPrice.objects.create(
                coin_id=str(i),
                name="Coin_3",
                symbol="coin_3",
                price=500,
                market_cap=1000000,
                total_volume=1000000,
                price_change_percentage_24h=10,
                snapshot=snapshot_2,
            )
            CoinPrice.objects.create(
                coin_id=str(i),
                name="Coin_4",
                symbol="coin_4",
                price=1500,
                market_cap=1000000,
                total_volume=1000000,
                price_change_percentage_24h=10,
                snapshot=snapshot_2,
            )

    def test_coin_price_history_count_sql_queries(self):
        """Проверяет количество запросов при получении истории цены"""
        # Без select_related 12 запросов
        # Если вместо Cursor использовать PageNumber + 1 запрос
        with self.assertNumQueries(1):
            response = self.client.get("/api/v1/coins/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_coin_price_history_filter_symbol(self):
        """Проверяет фильтрацию истории цены"""
        response = self.client.get("/api/v1/coins/?symbol=coin_2")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data["results"]:
            self.assertEqual(item["symbol"], "coin_2")

    def test_coin_price_history_filter_min_max_price(self):
        """Проверяет фильтрацию истории цены по минимальной и максимальной цене"""
        response = self.client.get("/api/v1/coins/?min_price=500&max_price=1500")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data["results"]:
            price = float(item["price"])
            self.assertGreaterEqual(price, 500)
            self.assertLessEqual(price, 1500)

    def test_coin_price_history_filter_min_max_price_edge_case(self):
        """Проверяет фильтрацию истории цены edge case"""
        snapshot_3 = Snapshot.objects.create()
        CoinPrice.objects.create(
            coin_id="test_case",
            name="Coin_test_case",
            symbol="coin_test_case",
            price=1499,
            market_cap=1000000,
            total_volume=1000000,
            price_change_percentage_24h=10,
            snapshot=snapshot_3,
        )
        response = self.client.get("/api/v1/coins/?min_price=501&max_price=1499")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 6)
        for item in response.data["results"]:
            price = float(item["price"])
            self.assertGreaterEqual(price, 501)
            self.assertLessEqual(price, 1499)
