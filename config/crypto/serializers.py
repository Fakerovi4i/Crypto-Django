from rest_framework import serializers

from crypto.models import CoinPrice, Snapshot, WatchlistItem


class CoinPriceSerializer(serializers.ModelSerializer):
    """Вложенный сериализатор для SnapshotSerializer, AnalyticsTopMoversApi"""

    class Meta:
        model = CoinPrice
        fields = ["coin_id", "name", "symbol", "price", "market_cap", "total_volume", "price_change_percentage_24h"]


class SnapshotListSerializer(serializers.ModelSerializer):
    """Сериализатор для Snapshot api/snapshots"""

    total_market_cap = serializers.DecimalField(max_digits=30, decimal_places=2, read_only=True, allow_null=True)

    class Meta:
        model = Snapshot
        fields = ["id", "created_at", "source", "total_market_cap"]


class SnapshotDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для Snapshot c монетами api/snapshots/{id}"""

    coin_prices = CoinPriceSerializer(many=True, read_only=True)
    total_market_cap = serializers.DecimalField(max_digits=30, decimal_places=2, read_only=True, allow_null=True)

    class Meta:
        model = Snapshot
        fields = ["id", "created_at", "total_market_cap", "source", "coin_prices"]


class CoinPriceHistorySerializer(serializers.ModelSerializer):
    """Сериализатор для CoinPriceHistory api/coins"""

    snapshot_date = serializers.DateTimeField(source="snapshot.created_at", read_only=True)
    # DRF: у базового Field уже есть атрибут source, имя поля менять нельзя (контракт API)
    source = serializers.CharField(source="snapshot.source", read_only=True)  # type: ignore[assignment]

    class Meta:
        model = CoinPrice
        fields = ["id", "name", "symbol", "price", "price_change_percentage_24h", "snapshot_date", "source"]


class WatchlistItemSerializer(serializers.ModelSerializer):
    """Сериализатор для WatchlistItem api/watchlist"""

    class Meta:
        model = WatchlistItem
        fields = ["id", "coin_symbol"]


class AnalyticsMarketStatsSerializer(serializers.Serializer):
    """Сериализатор для AnalyticsMarketStatsSerializer api/analytics/market-stats"""

    min_price = serializers.DecimalField(max_digits=20, decimal_places=8)
    max_price = serializers.DecimalField(max_digits=20, decimal_places=8)
    avg_price = serializers.DecimalField(max_digits=20, decimal_places=8)
    total_market_cap = serializers.DecimalField(max_digits=30, decimal_places=2)
