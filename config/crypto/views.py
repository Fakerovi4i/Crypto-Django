from typing import Any, cast

from celery.result import AsyncResult
from django.contrib.auth.models import User
from django.db.models import QuerySet
from rest_framework import status, views, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer

from crypto.decorators import handle_not_found
from crypto.models import CoinPrice, Snapshot
from crypto.serializers import (
    AnalyticsMarketStatsSerializer,
    CoinPriceFilterSerializer,
    CoinPriceHistorySerializer,
    CoinPriceSerializer,
    SnapshotDetailSerializer,
    SnapshotListSerializer,
    WatchlistItemSerializer,
)
from crypto.services import (
    analytics_market_stats,
    analytics_top_movers,
    analytics_volume_leaders,
    watchlist_item_add,
    watchlist_item_delete,
    watchlist_items_list,
)
from crypto.tasks import fetch_snapshot_task


class SnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление для Snapshot с вариантом списка и детализации"""

    queryset = Snapshot.objects.all()

    # Переопределяем метод get_serializer_class для возвращения разных сериализаторов в зависимости от действия
    def get_serializer_class(self) -> type[ModelSerializer]:
        if self.action == "list":
            return SnapshotListSerializer
        # Тут вызывается retrieve
        return SnapshotDetailSerializer


class CoinPriceHistory(viewsets.ReadOnlyModelViewSet):
    """Представление для истории цены"""

    queryset = CoinPrice.objects.select_related("snapshot")
    serializer_class = CoinPriceHistorySerializer

    def get_queryset(self) -> QuerySet[CoinPrice]:
        queryset = super().get_queryset()
        filters = CoinPriceFilterSerializer(data=self.request.query_params)
        filters.is_valid(raise_exception=True)

        data = filters.validated_data
        if "symbol" in data:
            queryset = queryset.filter(symbol__iexact=data["symbol"])
        if "min_price" in data:
            queryset = queryset.filter(price__gte=data["min_price"])
        if "max_price" in data:
            queryset = queryset.filter(price__lte=data["max_price"])

        return queryset.order_by("snapshot__source", "snapshot__created_at")


class WatchlistViewSet(viewsets.ViewSet):
    """Представление для Watchlist"""

    permission_classes = (IsAuthenticated,)

    def create(self, request: Request) -> Response:
        input_serializer = WatchlistItemSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        try:
            item = watchlist_item_add(
                user=cast(User, request.user), symbol=input_serializer.validated_data["coin_symbol"]
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        output_serializer = WatchlistItemSerializer(item)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request: Request) -> Response:
        items = watchlist_items_list(user=cast(User, request.user))
        serializer = WatchlistItemSerializer(items, many=True)
        return Response(serializer.data)

    def destroy(self, request: Request, pk: str) -> Response:
        try:
            watchlist_item_delete(user=cast(User, request.user), item_id=pk)
        except ValueError as e:
            return Response(data={"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AnalyticsMarketStatsApi(views.APIView):
    """GET /api/analytics/market-stats/ — статистика по последнему снапшоту"""

    @handle_not_found
    def get(self, request) -> Response:
        stats = analytics_market_stats()
        serializer = AnalyticsMarketStatsSerializer(stats)
        return Response(serializer.data)


class AnalyticsTopMoversApi(views.APIView):
    """GET /api/analytics/top-movers/ — топ-10 монет по изменению цены за 24ч"""

    @handle_not_found
    def get(self, request: Request) -> Response:
        top_movers = analytics_top_movers()
        serializer = CoinPriceSerializer(top_movers, many=True)
        return Response(serializer.data)


class AnalyticsVolumeLeadersApi(views.APIView):
    """GET /api/analytics/volume-leaders/ — топ-10 монет по объёму торгов"""

    @handle_not_found
    def get(self, request: Request) -> Response:
        coin_leaders = analytics_volume_leaders()
        serializer = CoinPriceSerializer(coin_leaders, many=True)
        return Response(serializer.data)


class FetchSnapshotApi(views.APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request) -> Response:
        result = fetch_snapshot_task.delay()
        return Response({"task_id": result.id}, status=status.HTTP_202_ACCEPTED)


class FetchSnapshotStatusApi(views.APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, task_id: str) -> Response:
        result: AsyncResult[Any] = AsyncResult(task_id)
        return Response({"task_id": result.id, "status": result.status, "result": str(result.result)})
