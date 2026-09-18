from rest_framework import generics, viewsets
from rest_framework.pagination import PageNumberPagination

from crypto.models import Snapshot, CoinPrice
from crypto.serializers import CoinPriceHistorySerializer, SnapshotListSerializer, SnapshotDetailSerializer


class SnapshotViewSet(viewsets.ModelViewSet):
    """Представление для Snapshot с вариантом списка и детализации"""
    queryset = Snapshot.objects.all()

    # Переопределяем метод get_serializer_class для возвращения разных сериализаторов в зависимости от действия
    def get_serializer_class(self):
        if self.action == 'list':
            return SnapshotListSerializer
        # Тут вызывается retrieve
        return SnapshotDetailSerializer


class CoinPriceHistory(viewsets.ReadOnlyModelViewSet):
    queryset = CoinPrice.objects.all()
    serializer_class = CoinPriceHistorySerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        symbol = self.request.query_params.get('symbol')
        if symbol:
            queryset = queryset.filter(symbol__iexact=symbol)
        return queryset.order_by('snapshot__source', 'snapshot__created_at', 'id')



