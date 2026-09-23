from abc import ABC, abstractmethod

from crypto.providers.connector import Connector
from crypto.providers.entities import Coin


class BaseProvider(ABC):
    def __init__(
            self,
            connector: Connector,
            host: str
    ):
        self.connector = connector
        self.host = host


    def __enter__(self):
        self.connector.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.connector.__exit__(exc_type, exc_val, exc_tb)

    @abstractmethod
    def get_coins(self, params: dict | None) -> list[Coin]:
        pass

    @abstractmethod
    def fetch_raw(self, params: dict) -> list[dict]:
        pass

    @classmethod
    def build_headers(cls) -> dict | None:
        return None

    @abstractmethod
    def symbol_exists(self, symbol: str) -> bool:
        pass