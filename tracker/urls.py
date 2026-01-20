from django.urls import path
from .views import pixel, stats, stats_marat

urlpatterns = [
    path("t.gif", pixel, name="pixel"),
    path("api/stats", stats, name="stats"),
    path("api/stats-marat", stats_marat, name="tracker_stats_marat"),

]
