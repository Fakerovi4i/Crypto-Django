from rest_framework import serializers
from crypto.models import Snapshot, CoinPrice


class CoinPriceSerializer(serializers.ModelSerializer):
    """Вложенный сериализатор для SnapshotSerializer"""
    class Meta:
        model = CoinPrice
        fields = '__all__'


class SnapshotListSerializer(serializers.ModelSerializer):
    """Сериализатор для Snapshot api/snapshots"""

    class Meta:
        model = Snapshot
        fields = ['id', 'created_at', 'source']


class SnapshotDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для Snapshot c монетами api/snapshots/{id}"""
    coin_prices = CoinPriceSerializer(many=True, read_only=True)

    class Meta:
        model = Snapshot
        fields = ['id', 'created_at', 'source', 'coin_prices']


class CoinPriceHistorySerializer(serializers.ModelSerializer):
    """Сериализатор для CoinPriceHistory api/coins"""
    snapshot_date = serializers.DateTimeField(source='snapshot.created_at', read_only=True)
    source = serializers.CharField(source='snapshot.source', read_only=True)

    class Meta:
        model = CoinPrice
        fields = ['id', 'name', 'symbol', 'price', 'price_change_percentage_24h', 'snapshot_date', 'source']