# content/api/filters.py
from django.db.models import Q
from django_filters import rest_framework as filters
from content.models import Post, Lesson, Event


class PostFilter(filters.FilterSet):
    category_slug = filters.CharFilter(field_name="category__slug", lookup_expr="iexact")
    q = filters.CharFilter(method="filter_q")

    class Meta:
        model = Post
        fields = {
            "status": ["exact"],
            "featured": ["exact"],
            "category": ["exact"],  # FK id
            "published_at": ["exact", "lt", "gt", "lte", "gte"],
        }

    def filter_q(self, queryset, name, value):
        return queryset.filter(
            Q(title__icontains=value) |
            Q(excerpt__icontains=value) |
            Q(content__icontains=value)
        )


class LessonFilter(filters.FilterSet):
    series = filters.NumberFilter(field_name="series_id")
    q = filters.CharFilter(method="filter_q")
    # published ni option ya ziada — itatumika tu kama model ina is_published
    published = filters.BooleanFilter(method="filter_published")

    class Meta:
        model = Lesson
        fields = {
            "series": ["exact"],
            "created_at": ["exact", "lt", "gt", "lte", "gte"],
            "updated_at": ["exact", "lt", "gt", "lte", "gte"],
            "views": ["exact", "lt", "gt", "lte", "gte"],
        }

    def filter_q(self, queryset, name, value):
        return queryset.filter(Q(title__icontains=value) | Q(description__icontains=value))

    def filter_published(self, queryset, name, value):
        if hasattr(Lesson, "is_published"):
            return queryset.filter(is_published=value)
        return queryset


class EventFilter(filters.FilterSet):
    q = filters.CharFilter(method="filter_q")
    date_from = filters.DateFilter(method="filter_date_from")
    date_to = filters.DateFilter(method="filter_date_to")

    class Meta:
        model = Event
        fields = []  # usiorodheshe fields zisizo kwenye model

    def _date_field(self):
        # tumia field halisi iliyopo kwenye model
        if hasattr(Event, "date"):
            return "date"
        if hasattr(Event, "start_date"):
            return "start_date"
        if hasattr(Event, "starts_at"):
            return "starts_at"
        return None

    def filter_q(self, queryset, name, value):
        return queryset.filter(Q(title__icontains=value) | Q(location__icontains=value))

    def filter_date_from(self, queryset, name, value):
        f = self._date_field()
        return queryset.filter(**{f + "__gte": value}) if f else queryset

    def filter_date_to(self, queryset, name, value):
        f = self._date_field()
        return queryset.filter(**{f + "__lte": value}) if f else queryset
