from rest_framework import viewsets, status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from crypto.models import Snapshot, CoinPrice
from crypto.serializers import CoinPriceHistorySerializer, SnapshotListSerializer, SnapshotDetailSerializer, \
    WatchlistItemSerializer, AnalyticsMarketStatsSerializer
from crypto.services import watchlist_item_add, watchlist_items_list, watchlist_item_delete, analytics_market_stats


class SnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление для Snapshot с вариантом списка и детализации"""
    queryset = Snapshot.objects.all()

    # Переопределяем метод get_serializer_class для возвращения разных сериализаторов в зависимости от действия
    def get_serializer_class(self):
        if self.action == 'list':
            return SnapshotListSerializer
        # Тут вызывается retrieve
        return SnapshotDetailSerializer


class CoinPriceHistory(viewsets.ReadOnlyModelViewSet):
    """Представление для истории цены"""
    queryset = CoinPrice.objects.select_related('snapshot')
    serializer_class = CoinPriceHistorySerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        symbol = self.request.query_params.get('symbol')
        if symbol:
            queryset = queryset.filter(symbol__iexact=symbol)

        return queryset.order_by('snapshot__source', 'snapshot__created_at')


class WatchlistViewSet(viewsets.ViewSet):
    """Представление для Watchlist"""
    permission_classes = (IsAuthenticated,)

    def create(self, request):
        input_serializer = WatchlistItemSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        try:
            item = watchlist_item_add(
                user=request.user,
                symbol=input_serializer.validated_data['coin_symbol']
            )
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        output_serializer = WatchlistItemSerializer(item)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request):
        items = watchlist_items_list(user=request.user)
        serializer = WatchlistItemSerializer(items, many=True)
        return Response(serializer.data)

    def destroy(self, request, pk=None):
        try:
            watchlist_item_delete(user=request.user, item_id=pk)
        except ValueError as e:
            return Response(data={'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AnalyticsMarketStatsApi(views.APIView):
    """GET /api/analytics/market-stats/ — статистика по последнему снапшоту"""
    def get(self, request):
        try:
            stats = analytics_market_stats()
        except ValueError as e:
            return Response(data={'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = AnalyticsMarketStatsSerializer(stats)
        return Response(serializer.data)
