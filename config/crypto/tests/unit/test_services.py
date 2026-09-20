from unittest.mock import patch, MagicMock

from django.contrib.auth.models import User
from django.test import TestCase

from crypto.models import WatchlistItem
from crypto.services import watchlist_item_add, watchlist_items_list, watchlist_item_delete


class WatchlistServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_1', password='123')

    @patch('crypto.services.get_provider')
    def test_watchlist_item_add_create_valid_symbol(self, mock_get_provider):
        """Проверяет, что добавление в монеты с существующим символом работает корректно"""
        mock_provider = MagicMock()
        mock_provider.__enter__.return_value = mock_provider
        mock_provider.symbol_exists.return_value = True
        mock_get_provider.return_value = mock_provider

        item = watchlist_item_add(user=self.user, symbol='btc')

        self.assertEqual(item.coin_symbol, 'btc')
        self.assertEqual(item.user, self.user)
        self.assertEqual(WatchlistItem.objects.count(), 1)


    @patch('crypto.services.get_provider')
    def test_watchlist_item_add_create_invalid_symbol(self, mock_get_provider):
        """Проверяет, что добавление в монеты с несуществующим символом выдает ошибку"""
        mock_provider = MagicMock()
        mock_provider.__enter__.return_value = mock_provider
        mock_provider.symbol_exists.return_value = False
        mock_get_provider.return_value = mock_provider

        with self.assertRaises(ValueError):
            watchlist_item_add(user=self.user, symbol='btc')

        self.assertEqual(WatchlistItem.objects.count(), 0)


    def test_watchlist_items_list_returns_only_user_items(self):
        """Проверяет, что список монет возвращает только собственные"""
        other_user = User.objects.create_user(username='test_2', password='123')

        WatchlistItem.objects.create(user=self.user, coin_symbol='btc')
        WatchlistItem.objects.create(user=self.user, coin_symbol='eth')
        WatchlistItem.objects.create(user=other_user, coin_symbol='sol')

        items = watchlist_items_list(user=self.user)

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].coin_symbol, 'btc')
        self.assertEqual(items[1].coin_symbol, 'eth')

    def test_watchlist_item_delete_not_delete_other_item(self):
        """Проверяет, что удаляется только собственная монета"""
        other_user = User.objects.create_user(username='test_2', password='123')
        other_item = WatchlistItem.objects.create(user=other_user, coin_symbol='eth')

        watchlist_item_delete(user=self.user, item_id=other_item.pk)

        self.assertTrue(WatchlistItem.objects.filter(pk=other_item.pk).exists())
