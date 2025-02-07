from django_filters import rest_framework as filters
from .models import Action

class ActionFilter(filters.FilterSet):
    created = filters.DateFromToRangeFilter()

    class Meta:
        model = Action
        fields = ['created']
