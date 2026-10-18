import threading
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase, TransactionTestCase

from crypto.models import Balance, CoinPrice, Portfolio, Snapshot
from crypto.services import PortfolioService


class PortfolioServiceTests(TestCase):
    def setUp(self):
        self.user_1 = User.objects.create_user(username="user_1", password="1234")
        self.user_2 = User.objects.create_user(username="user_2", password="1234")

        Balance.objects.update_or_create(user=self.user_1, defaults={"amount": Decimal("1000")})
        Balance.objects.update_or_create(user=self.user_2, defaults={"amount": Decimal("1000")})

        Portfolio.objects.create(user=self.user_2, symbol="btc", amount=Decimal("1"), buy_price=Decimal("1000"))

        snapshot = Snapshot.objects.create()
        CoinPrice.objects.create(
            coin_id="bitcoin",
            name="Bitcoin",
            symbol="btc",
            price=Decimal("1000"),
            market_cap=Decimal("1000"),
            total_volume=Decimal("1000"),
            price_change_percentage_24h=Decimal("1"),
            snapshot=snapshot,
        )

    def test_success_transaction(self):
        """Проверка на успешную транзакцию"""
        PortfolioService().buy(user=self.user_1, symbol="btc", amount=Decimal("1"))

        balance = Balance.objects.get(user=self.user_1)
        self.assertEqual(balance.amount, Decimal("0"))

        portfolio = Portfolio.objects.get(user=self.user_1, symbol="btc")
        self.assertEqual(portfolio.amount, Decimal("1"))

    def test_not_enough_balance_value_error(self):
        """Проверка на недостаточное количество средств 2 монеты по 1000 не проходят"""

        with self.assertRaises(ValueError):
            PortfolioService().buy(user=self.user_1, symbol="btc", amount=Decimal("2"))

        balance = Balance.objects.get(user=self.user_1)

        self.assertEqual(balance.amount, Decimal("1000"))
        self.assertFalse(Portfolio.objects.filter(user=self.user_1).exists())

    def test_success_sell_balance_up_portfolio_down(self):
        """Проверка на успешную продажу"""
        PortfolioService().sell(user=self.user_2, symbol="btc", amount=Decimal("0.5"))

        balance = Balance.objects.get(user=self.user_2)
        portfolio = Portfolio.objects.get(user=self.user_2, symbol="btc")

        self.assertEqual(balance.amount, Decimal("1500"))
        self.assertEqual(portfolio.amount, Decimal("0.5"))

        PortfolioService().sell(user=self.user_2, symbol="btc", amount=Decimal("0.5"))

        self.assertFalse(Portfolio.objects.filter(user=self.user_2, symbol="btc").exists())


class PortfolioServiseSelectForUpdateTests(TransactionTestCase):
    def setUp(self):
        self.user_race = User.objects.create_user(username="user_race", password="1234")
        Balance.objects.update_or_create(user=self.user_race, defaults={"amount": Decimal("1100")})
        snapshot = Snapshot.objects.create()
        CoinPrice.objects.create(
            coin_id="bitcoin",
            name="Bitcoin",
            symbol="btc",
            price=Decimal("1000"),
            market_cap=Decimal("1000"),
            total_volume=Decimal("1000"),
            price_change_percentage_24h=Decimal("1"),
            snapshot=snapshot,
        )

    def test_by_only_one_select_for_update_is_working(self):
        results = []
        barrier = threading.Barrier(2)

        def worker():
            try:
                barrier.wait()
                PortfolioService().buy(user=self.user_race, symbol="btc", amount=Decimal("1"))
                results.append("ok")
            except ValueError as e:
                results.append(str(e))
            finally:
                connection.close()

        threads = [threading.Thread(target=worker) for _ in range(2)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        self.assertEqual(results, ["ok", "Not enough balance"])
        self.assertEqual(Balance.objects.get(user=self.user_race).amount, Decimal("100"))
        self.assertEqual(Portfolio.objects.get(user=self.user_race, symbol="btc").amount, Decimal("1"))
