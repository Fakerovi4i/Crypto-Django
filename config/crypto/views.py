from rest_framework import generics, viewsets
from rest_framework.pagination import PageNumberPagination

from crypto.models import Snapshot, CoinPrice
from crypto.serializers import SnapshotSerializer, CoinPriceHistorySerializer


class SnapshotPagination(PageNumberPagination):
    page_size = 1


class CoinPricePagination(PageNumberPagination):
    page_size = 10


class SnapshotViewSet(viewsets.ModelViewSet):
    queryset = Snapshot.objects.all()
    serializer_class = SnapshotSerializer
    pagination_class = SnapshotPagination


class CoinPriceHistory(viewsets.ReadOnlyModelViewSet):
    queryset = CoinPrice.objects.all()
    serializer_class = CoinPriceHistorySerializer
    pagination_class = CoinPricePagination

    def get_queryset(self):
        queryset = super().get_queryset()
        symbol = self.request.query_params.get('symbol')
        if symbol:
            queryset = queryset.filter(symbol__iexact=symbol)
        return queryset.order_by('snapshot__source', 'snapshot__created_at')



