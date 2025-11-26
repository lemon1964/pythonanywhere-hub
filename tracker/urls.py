from django.urls import path
from .views import pixel, stats

urlpatterns = [
    path("t.gif", pixel, name="pixel"),
    path("api/stats", stats, name="stats"),
]
