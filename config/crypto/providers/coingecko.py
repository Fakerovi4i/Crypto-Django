from crypto.providers.base import BaseProvider
from crypto.providers.connector import Connector
from crypto.providers.entities import Coin


class ProviderCoingecko(BaseProvider):
    HOST = "https://api.coingecko.com"
    MARKETS_PATH = "/api/v3/coins/markets"
    SIMPLE_PRICE_PATH = "/api/v3/simple/price"

    def __init__(self, connector: Connector, host: str = HOST):
        super().__init__(connector, host)

    def get_coins(self, params: dict | None = None) -> list[Coin]:
        if params is None:
            params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 50, "page": 1}

        raw_data = self.fetch_raw(params)
        coins = [
            Coin(
                id=item["id"],
                name=item["name"],
                symbol=item["symbol"],
                price_change_percentage_24h=item["price_change_percentage_24h"],
                total_volume=item["total_volume"],
                market_cap=item["market_cap"],
                price=item["current_price"]
            )
            for item in raw_data
        ]
        return coins


    def fetch_raw(self, params: dict) -> list[dict]:
        url = self.host + self.MARKETS_PATH
        response: list[dict] = self.connector.get(url=url, params=params)
        return response


    def symbol_exists(self, symbol: str) -> bool:
        url = self.host + self.SIMPLE_PRICE_PATH
        params = {"vs_currencies": "usd", "symbols": symbol}
        response: dict = self.connector.get(url=url, params=params)

        if response:
            return True

        return False