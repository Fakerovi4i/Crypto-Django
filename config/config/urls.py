from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from crypto.views import SnapshotViewSet, CoinPriceHistory


admin.site.site_header = "Панель администрирования"
admin.site.index_title = "Анализатор крипто-валют"

router = DefaultRouter()
router.register(r'snapshots', SnapshotViewSet)
router.register(r'coins', CoinPriceHistory)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls))
]


