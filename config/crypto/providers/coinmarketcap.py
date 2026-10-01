import os

from crypto.providers.base import BaseProvider
from crypto.providers.connector import Connector
from crypto.providers.entities import Coin


class ProviderCMC(BaseProvider):
    HOST = "https://pro-api.coinmarketcap.com"
    MARKETS_PATH = "/v3/cryptocurrency/listings/latest"
    SIMPLE_PRICE_PATH = "/v2/simple/price"

    def __init__(
        self,
        connector: Connector,
        host: str = HOST,
    ):
        super().__init__(connector, host)

    @classmethod
    def build_headers(cls) -> dict | None:
        return {"Accept": "application/json", "X-CMC_PRO_API_KEY": os.getenv("API_KEY")}

    def get_coins(self, params: dict | None = None) -> list[Coin]:
        if params is None:
            params = {"sort": "market_cap", "sort_dir": "desc", "limit": "50"}

        raw_data: list[dict] = self.fetch_raw(params)
        coins = [
            Coin(
                id=item["id"],
                name=item["name"],
                symbol=item["symbol"],
                price_change_percentage_24h=item["quote"][0]["percent_change_24h"],
                total_volume=item["quote"][0]["volume_24h"],
                market_cap=item["quote"][0]["market_cap"],
                price=item["quote"][0]["price"],
            )
            for item in raw_data
        ]
        return coins

    def fetch_raw(self, params: dict) -> list[dict]:
        url = self.host + self.MARKETS_PATH
        response: dict = self.connector.get(url=url, params=params)
        return response["data"]

    def symbol_exists(self, symbol: str) -> bool:
        url = self.host + self.SIMPLE_PRICE_PATH
        params = {"symbol": symbol}
        response: dict = self.connector.get(url=url, params=params)

        if response:
            return True

        return False
