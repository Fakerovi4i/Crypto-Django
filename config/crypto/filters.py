import django_filters

from crypto.models import CoinPrice


class CoinPriceFilter(django_filters.FilterSet):
    symbol = django_filters.CharFilter(field_name="symbol", lookup_expr="iexact")
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")

    class Meta:
        model = CoinPrice
        fields = ["symbol", "min_price", "max_price"]
