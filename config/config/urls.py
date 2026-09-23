from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from crypto.views import SnapshotViewSet, CoinPriceHistory, WatchlistViewSet, AnalyticsMarketStatsApi, \
    AnalyticsTopMoversApi

admin.site.site_header = "Панель администрирования"
admin.site.index_title = "Анализатор крипто-валют"

router = DefaultRouter()
router.register(r'snapshots', SnapshotViewSet)
router.register(r'coins', CoinPriceHistory)
router.register(r'watchlist', WatchlistViewSet, basename='watchlist')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('__debug__/', include('debug_toolbar.urls')),
    path('api/analytics/market-stats/', AnalyticsMarketStatsApi.as_view(), name='analytics_market_stats'),
    path('api/analytics/top-movers/', AnalyticsTopMoversApi.as_view(), name='analytics_top_movers'),
]


