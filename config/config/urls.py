from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

admin.site.site_header = "Панель администрирования"
admin.site.index_title = "Анализатор крипто-валют"


urlpatterns = [
    path("admin/", admin.site.urls),
    # ─── Инфраструктура (без версии) ───
    path("api-auth/", include("rest_framework.urls")),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("__debug__/", include("debug_toolbar.urls")),
    # ─── Версионированное API ───
    path("api/<str:version>/", include("crypto.api_urls")),
]
