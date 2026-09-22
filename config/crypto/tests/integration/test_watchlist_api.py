from unittest.mock import patch, MagicMock

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from crypto.models import WatchlistItem
from crypto.tests.helpers import make_mock_provider


class WatchlistApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user_1', password='1234')
        self.other_user = User.objects.create_user(username='user_2', password='12345')

        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')


    def test_unauthenticated_request_401(self):
        """Проверяет, что неавторизованный запрос возвращает 401"""
        self.client.credentials()
        response = self.client.get('/api/watchlist/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    @patch('crypto.services.get_provider')
    def test_success_add_item(self, mock_get_provider):
        """Проверяет, что добавление в монеты работает корректно"""
        mock_get_provider.return_value = make_mock_provider(symbol_exists=True)

        response = self.client.post('/api/watchlist/', {'coin_symbol': 'btc'})


        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(WatchlistItem.objects.count(), 1)
        self.assertEqual(WatchlistItem.objects.get().coin_symbol, 'btc')


    @patch('crypto.services.get_provider')
    def test_invalid_symbol_raise_400(self, mock_get_provider):
        """Проверяет, что добавление в монеты с несуществующим символом возвращает 400"""
        mock_provider = MagicMock()
        mock_provider.__enter__.return_value = mock_provider
        mock_provider.symbol_exists.return_value = False
        mock_get_provider.return_value = mock_provider

        response = self.client.post('/api/watchlist/', {'symbol': 'not_valid_symbol'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(WatchlistItem.objects.count(), 0)

    def test_user_can_see_only_own_items(self):
        """Проверяет, что пользователь может видеть только свои монеты"""
        WatchlistItem.objects.create(user=self.user, coin_symbol='eth')
        WatchlistItem.objects.create(user=self.other_user, coin_symbol='sol')

        response = self.client.get('/api/watchlist/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['coin_symbol'], 'eth')

    def test_not_delete_other_item(self):
        """Проверяет, что пользователь не может удалить чужую монету"""
        other_item = WatchlistItem.objects.create(user=self.other_user, coin_symbol='sol')

        # user try delete other_user item
        response = self.client.delete(f'/api/watchlist/{other_item.pk}/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(WatchlistItem.objects.count(), 1)
        self.assertTrue(WatchlistItem.objects.filter(pk=other_item.pk).exists())


    def test_obtain_and_refresh_token(self):
        self.client.credentials()  # необходима валидация
        response = self.client.post('/api/token/', {'username': 'user_1', 'password': '1234'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

        refresh_response = self.client.post('/api/token/refresh/', {'refresh': response.data['refresh']})
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)