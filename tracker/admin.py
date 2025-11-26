from django.contrib import admin
from django.db.models import F

from .models import Counter


@admin.action(description="Обнулить счётчики (count = 0) для выбранных")
def reset_selected_counters(modeladmin, request, queryset):
    queryset.update(count=0)


@admin.action(description="Прибавить +1 к выбранным (тест)")
def increment_selected_counters(modeladmin, request, queryset):
    queryset.update(count=F("count") + 1)


@admin.register(Counter)
class CounterAdmin(admin.ModelAdmin):
    list_display = ("event", "src", "count", "updated_at")
    list_filter = ("src", "event")
    search_fields = ("event", "src")
    ordering = ("-count",)
    actions = (reset_selected_counters, increment_selected_counters)
