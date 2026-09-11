from dataclasses import dataclass


@dataclass
class Coin:
    id: str | int
    name: str
    symbol: str
    price_change_percentage_24h: float
    total_volume: float
    market_cap: float
    price: float

    def __post_init__(self):
        if not isinstance(self.id, (str, int)) or not str(self.id).strip():
            raise ValueError("id must be a string or integer")
        if not isinstance(self.price, (int, float)):
            raise ValueError("price must be a number")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("name must be a string")
        if not isinstance(self.symbol, str) or not self.symbol.strip():
            raise ValueError("symbol must be a string")
        if not isinstance(self.total_volume, (int, float)):
            raise ValueError("total_volume must be a number")
        if not isinstance(self.market_cap, (int, float)):
            raise ValueError("market_cap must be a number")
        if self.total_volume < 0:
            raise ValueError("total_volume must not be negative")
        if self.market_cap < 0:
            raise ValueError("market_cap must not be negative")
        if self.price_change_percentage_24h is None:
            self.price_change_percentage_24h = 0.0
        elif not isinstance(self.price_change_percentage_24h, (int, float)):
            raise ValueError("price_change_percentage_24h must be a number")


    def __str__(self):
        return (
            f"class: {self.__class__.__name__} | "
            f"name: {self.name} | "
            f"id: {self.id} | "
            f"price_change_24: {self.price_change_percentage_24h} | "
            f"price: {self.price}"
        )

    def __lt__(self, other):
        return self.price_change_percentage_24h < other.price_change_percentage_24h