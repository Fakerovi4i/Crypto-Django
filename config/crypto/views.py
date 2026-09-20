from rest_framework import viewsets, views, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from crypto.models import Snapshot, CoinPrice, WatchlistItem
from crypto.serializers import CoinPriceHistorySerializer, SnapshotListSerializer, SnapshotDetailSerializer, \
    WatchlistItemSerializer
from crypto.services import watchlist_item_add, watchlist_items_list, watchlist_item_delete


class SnapshotPagination(PageNumberPagination):
    page_size = 10


class CoinPricePagination(PageNumberPagination):
    page_size = 10


class SnapshotViewSet(viewsets.ModelViewSet):
    """Представление для Snapshot с вариантом списка и детализации"""
    queryset = Snapshot.objects.all()
    pagination_class = SnapshotPagination

    # Переопределяем метод get_serializer_class для возвращения разных сериализаторов в зависимости от действия
    def get_serializer_class(self):
        if self.action == 'list':
            return SnapshotListSerializer
        # Тут вызывается retrieve
        return SnapshotDetailSerializer


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


class WatchlistViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    def create(self, request):
        try:
            item = watchlist_item_add(user=request.user, symbol=request.data.get('symbol'))
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = WatchlistItemSerializer(item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request):
        items = watchlist_items_list(user=request.user)
        serializer = WatchlistItemSerializer(items, many=True)
        return Response(serializer.data)

    def destroy(self, request, pk=None):
        watchlist_item_delete(user=request.user, item_id=pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


