from crypto.providers.base import BaseProvider
from crypto.providers.connector import Connector
from crypto.providers.entities import Coin


class ProviderCoingecko(BaseProvider):
    def __init__(
            self,
            connector: Connector,
            host: str = "https://api.coingecko.com",
            path: str = "/api/v3/coins/markets"
    ):
        super().__init__(connector, host, path)


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
        response: list[dict] = self.connector.get(url=self.url, params=params)
        return response