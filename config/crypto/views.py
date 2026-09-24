from rest_framework import viewsets, status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from crypto.models import Snapshot, CoinPrice
from crypto.serializers import CoinPriceHistorySerializer, SnapshotListSerializer, SnapshotDetailSerializer, \
    WatchlistItemSerializer, AnalyticsMarketStatsSerializer, CoinPriceSerializer, CoinPriceFilterSerializer

from crypto.services import watchlist_item_add, watchlist_items_list, watchlist_item_delete, analytics_market_stats, \
    analytics_top_movers, analytics_volume_leaders


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
        filters = CoinPriceFilterSerializer(data=self.request.query_params)
        filters.is_valid(raise_exception=True)

        data = filters.validated_data
        if 'symbol' in data:
            queryset = queryset.filter(symbol__iexact=data['symbol'])
        if 'min_price' in data:
            queryset = queryset.filter(price__gte=data['min_price'])
        if 'max_price' in data:
            queryset = queryset.filter(price__lte=data['max_price'])

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


class AnalyticsTopMoversApi(views.APIView):
    """GET /api/analytics/top-movers/ — топ-10 монет по изменению цены за 24ч"""

    def get(self, request):
        try:
            top_movers = analytics_top_movers()
        except ValueError as e:
            return Response(data={'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = CoinPriceSerializer(top_movers, many=True)
        return Response(serializer.data)


class AnalyticsVolumeLeaders(views.APIView):
    """GET /api/analytics/volume-leaders/ — топ-10 монет по объёму торгов"""

    def get(self, request):
        try:
            coin_leaders = analytics_volume_leaders()
        except ValueError as e:
            return Response(data={'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = CoinPriceSerializer(coin_leaders, many=True)
        return Response(serializer.data)