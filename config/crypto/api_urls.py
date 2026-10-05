from django.urls import include, path
from rest_framework.routers import DefaultRouter

from crypto.views import (
    AnalyticsMarketStatsApi,
    AnalyticsTopMoversApi,
    AnalyticsVolumeLeadersApi,
    CoinPriceHistory,
    FetchSnapshotApi,
    FetchSnapshotStatusApi,
    SnapshotViewSet,
    WatchlistViewSet,
)

router = DefaultRouter()
router.register(r"snapshots", SnapshotViewSet)
router.register(r"coins", CoinPriceHistory)
router.register(r"watchlist", WatchlistViewSet, basename="watchlist")

urlpatterns = [
    path("", include(router.urls)),
    path("analytics/market-stats/", AnalyticsMarketStatsApi.as_view(), name="analytics_market_stats"),
    path("analytics/top-movers/", AnalyticsTopMoversApi.as_view(), name="analytics_top_movers"),
    path("analytics/volume-leaders/", AnalyticsVolumeLeadersApi.as_view(), name="analytics_volume_leaders"),
    path("fetch-snapshot/", FetchSnapshotApi.as_view(), name="fetch_snapshot"),
    path("fetch-snapshot-status/<str:task_id>/", FetchSnapshotStatusApi.as_view(), name="fetch_snapshot_status"),
]
