from django_filters import rest_framework as filters
from .models import Image

class CharFilterInFilter(filters.BaseInFilter, filters.CharFilter):
    pass

class ImageFilter(filters.FilterSet):
    created = filters.DateFromToRangeFilter()
    category = filters.CharFilter(field_name='category__name', lookup_expr='iexact')
    tags = CharFilterInFilter(field_name='tags__name',  lookup_expr='in')

    class Meta:
        model = Image
        fields = ['created']
