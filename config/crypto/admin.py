from django.contrib import admin

from .models import Balance, CoinPrice, Portfolio, Snapshot, WatchlistItem


class CoinPriceInline(admin.TabularInline):
    model = CoinPrice
    extra = 0
    fields = ("coin_id", "name", "price", "price_change_percentage_24h")


@admin.register(Snapshot)
class SnapshotAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "source")
    list_display_links = ("id", "created_at")
    ordering = ("-created_at",)
    inlines = [CoinPriceInline]


@admin.register(CoinPrice)
class CoinPriceAdmin(admin.ModelAdmin):
    list_display = ("coin_id", "name", "price", "snapshot")
    ordering = ("price_change_percentage_24h",)


@admin.register(WatchlistItem)
class WatchlistItemAdmin(admin.ModelAdmin):
    list_display = ("id", "coin_symbol", "user")
    list_display_links = ("id",)
    ordering = ("-id",)


@admin.register(Balance)
class BalanceAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "amount")
    list_display_links = ("id",)
    ordering = ("-amount",)


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "symbol", "amount", "buy_price", "bought_at")
    list_display_links = ("id",)
    ordering = ("-bought_at",)
