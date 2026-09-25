from rest_framework import status
from rest_framework.test import APITestCase

from crypto.models import Snapshot, CoinPrice


class AnalyticsApiWithDataTests(APITestCase):
    """Снэпшот с монетами — проверка реальных значений"""
    def setUp(self):
        snapshot_1 = Snapshot.objects.create()
        snapshot_2 = Snapshot.objects.create()

        for i in range(1, 6):
            CoinPrice.objects.create(
                coin_id=str(i),
                name=f'Coin_{i}',
                symbol=f'coin_{i}',
                price=200 * i,
                market_cap=1000,
                total_volume=1000,
                price_change_percentage_24h=i,
                snapshot=snapshot_1
            )

            CoinPrice.objects.create(
                coin_id=str(i),
                name=f'Coin_{i}',
                symbol=f'coin_{i}',
                price=100 * i,
                market_cap=1000,
                total_volume=1000 * i,
                price_change_percentage_24h=i,
                snapshot=snapshot_2
            )

        CoinPrice.objects.create(
            coin_id=str('6'),
            name=f'Coin_6',
            symbol=f'coin_6',
            price=50,
            market_cap=500,
            total_volume=1000,
            price_change_percentage_24h=-10,
            snapshot=snapshot_2
        )


    def _create_coins_for_snapshot(self, snapshot, count):
        for i in range(1, count + 1):
            CoinPrice.objects.create(
                coin_id=f'test_{i}', name=f'Test_{i}', symbol=f'test_{i}',
                price=10, market_cap=10, total_volume=100 * i,
                price_change_percentage_24h=i, snapshot=snapshot
            )


    def test_analyticsmarket_stats_get_correct(self):
        """Проверяет, что запрос к market-stats возвращает корректные значения"""
        response = self.client.get('/api/analytics/market-stats/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['min_price']), 50)
        self.assertEqual(float(response.data['max_price']), 500)
        self.assertEqual(float(response.data['total_market_cap']), 5500)
        #258,33
        self.assertAlmostEqual(float(response.data['avg_price']), 1550 / 6, places=2)


    def test_analytics_top_movers_get_correct(self):
        """Проверяет, что запрос к top-movers возвращает корректные значения"""
        response = self.client.get('/api/analytics/top-movers/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 6)
        self.assertEqual(response.data[0]['name'], 'Coin_6')


    def test_analytics_volume_leaders_get_correct(self):
        """Проверяет, что запрос к volume-leaders возвращает корректные значения"""
        response = self.client.get('/api/analytics/volume-leaders/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 6)
        self.assertEqual(response.data[0]['name'], 'Coin_5')


    def test_analytics_volume_leaders_limited_to_10(self):
        """Проверяет лимит топа volume-leaders"""
        snapshot = Snapshot.objects.create()
        self._create_coins_for_snapshot(snapshot, 21)
        response = self.client.get('/api/analytics/volume-leaders/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 10)


    def test_analytics_top_movers_limited_to_10(self):
        """Проверяет лимит топа top-movers"""
        snapshot = Snapshot.objects.create()
        self._create_coins_for_snapshot(snapshot, 16)
        response = self.client.get('/api/analytics/top-movers/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 10)


class AnalyticsApiNoSnapshotsTests(APITestCase):
    """БД пуста, снэпшотов нет"""

    def test_analytics_market_stats_return_404(self):
        response = self.client.get('/api/analytics/market-stats/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'detail': 'No snapshots found'})


    def test_analytics_top_movers_return_404(self):
        response = self.client.get('/api/analytics/top-movers/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'detail': 'No snapshots found'})


    def test_analytics_volume_leaders_return_404(self):
        response = self.client.get('/api/analytics/volume-leaders/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'detail': 'No snapshots found'})


class AnalyticsApiEmptySnapshotTests(APITestCase):
    """Снэпшот есть, монет в нём нет"""
    def setUp(self):
        snapshot_1 = Snapshot.objects.create()


    def test_analyticsmarket_stats_returns_404_no_data(self):
        """Проверяет detail: No market data found"""
        response = self.client.get('/api/analytics/market-stats/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'detail': 'No market data found'})


    def test_analytics_top_movers_return_empty_list(self):
        """Проверка, что ответ 200, но в данных пусто для top-movers"""
        response = self.client.get('/api/analytics/top-movers/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])


    def test_analytics_volume_leaders_return_empty_list(self):
        """Проверка, что ответ 200, но в данных пусто для volume-leaders"""
        response = self.client.get('/api/analytics/volume-leaders/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])













