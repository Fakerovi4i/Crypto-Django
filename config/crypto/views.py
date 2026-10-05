from typing import Any, cast

from celery.result import AsyncResult
from django.contrib.auth.models import User
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers, status, views, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import CursorPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer

from crypto.decorators import handle_not_found
from crypto.filters import CoinPriceFilter
from crypto.models import CoinPrice, Snapshot
from crypto.permissions import IsAdminOrReadOnly
from crypto.serializers import (
    AnalyticsMarketStatsSerializer,
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


@extend_schema(tags=["Snapshot"])
@extend_schema_view(
    list=extend_schema(
        summary="Получить список снимков",
        responses=SnapshotListSerializer(many=True),
        parameters=[
            OpenApiParameter("ordering", type=str, description="created_at, total_market_cap, '-' обратный порядок")
        ],
    ),
    retrieve=extend_schema(summary="Получить детализацию снимка", responses=SnapshotDetailSerializer),
)
class SnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление для Snapshot с вариантом списка и детализации"""

    permission_classes = (AllowAny,)
    queryset = Snapshot.objects.annotate(total_market_cap=Sum("coin_prices__market_cap"))
    filter_backends = [OrderingFilter]
    ordering_fields = ["created_at", "total_market_cap"]
    ordering = ["-created_at"]

    # Переопределяем метод get_serializer_class для возвращения разных сериализаторов в зависимости от действия
    def get_serializer_class(self) -> type[ModelSerializer]:
        if self.action == "list":
            return SnapshotListSerializer
        # Тут вызывается retrieve
        return SnapshotDetailSerializer


class CoinPriceCursorPagination(CursorPagination):
    """Курсор Пагинатор для CoinPriceHistory"""

    page_size = 50
    ordering = "-id"


@extend_schema(tags=["CoinPriceHistory"])
@extend_schema_view(
    list=extend_schema(summary="Получить все монеты из всех снимков"),
    retrieve=extend_schema(summary="Получить монету по id"),
)
class CoinPriceHistory(viewsets.ReadOnlyModelViewSet):
    """Представление для истории цены"""

    queryset = CoinPrice.objects.select_related("snapshot")
    serializer_class = CoinPriceHistorySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = CoinPriceFilter
    search_fields = ["symbol", "name"]
    pagination_class = CoinPriceCursorPagination


@extend_schema(tags=["Watchlist"])
@extend_schema_view(
    create=extend_schema(summary="Добавить монету в watchlist", responses={201: WatchlistItemSerializer}),
    list=extend_schema(summary="Список монет в watchlist"),
    destroy=extend_schema(summary="Удалить монету из watchlist", responses={204: None}),
)
class WatchlistViewSet(viewsets.ViewSet):
    """Представление для Watchlist"""

    permission_classes = (IsAuthenticated,)
    # Для документации
    serializer_class = WatchlistItemSerializer

    def create(self, request: Request, *args, **kwargs) -> Response:
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

    def list(self, request: Request, *args, **kwargs) -> Response:
        items = watchlist_items_list(user=cast(User, request.user))
        serializer = WatchlistItemSerializer(items, many=True)
        return Response(serializer.data)

    def destroy(self, request: Request, pk: str, *args, **kwargs) -> Response:
        try:
            watchlist_item_delete(user=cast(User, request.user), item_id=pk)
        except ValueError as e:
            return Response(data={"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["Analytics"])
class AnalyticsMarketStatsApi(views.APIView):
    """GET /api/analytics/market-stats/ — статистика по последнему снапшоту"""

    @extend_schema(summary="Получить статистику по последнему снимку монет", responses=AnalyticsMarketStatsSerializer)
    @handle_not_found
    def get(self, request: Request, *args, **kwargs) -> Response:
        stats = analytics_market_stats()
        serializer = AnalyticsMarketStatsSerializer(stats)
        return Response(serializer.data)


@extend_schema(tags=["Analytics"])
class AnalyticsTopMoversApi(views.APIView):
    """GET /api/analytics/top-movers/ — топ-10 монет по изменению цены за 24ч"""

    @extend_schema(summary="Получить топ 10 монет по изменению за 24 часа", responses=CoinPriceSerializer(many=True))
    @handle_not_found
    def get(self, request: Request, *args, **kwargs) -> Response:
        top_movers = analytics_top_movers()
        serializer = CoinPriceSerializer(top_movers, many=True)
        return Response(serializer.data)


@extend_schema(tags=["Analytics"])
class AnalyticsVolumeLeadersApi(views.APIView):
    """GET /api/analytics/volume-leaders/ — топ-10 монет по объёму торгов"""

    @extend_schema(summary="Получить топ 10 монет по объему торгов", responses=CoinPriceSerializer(many=True))
    @handle_not_found
    def get(self, request: Request, *args, **kwargs) -> Response:
        coin_leaders = analytics_volume_leaders()
        serializer = CoinPriceSerializer(coin_leaders, many=True)
        return Response(serializer.data)


@extend_schema(tags=["FetchSnapshot"])
class FetchSnapshotApi(views.APIView):
    """Делает snapshot через celery worker"""

    permission_classes = (IsAdminOrReadOnly,)

    @extend_schema(
        summary="Запустить сбор снимка (только админ)",
        request=None,
        responses={202: inline_serializer("FetchSnapshotResponse", {"task_id": serializers.CharField()})},
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        result = fetch_snapshot_task.delay()
        return Response({"task_id": result.id}, status=status.HTTP_202_ACCEPTED)


@extend_schema(tags=["FetchSnapshot"])
class FetchSnapshotStatusApi(views.APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Получить статус задачи по id задачи",
        responses=inline_serializer(
            "FetchSnapshotStatusResponse",
            {"task_id": serializers.CharField(), "status": serializers.CharField(), "result": serializers.CharField()},
        ),
    )
    def get(self, request: Request, task_id: str, *args, **kwargs) -> Response:
        result: AsyncResult[Any] = AsyncResult(task_id)
        return Response({"task_id": result.id, "status": result.status, "result": str(result.result)})
