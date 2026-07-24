from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("health/", views.health, name="health"),
    path(
        "internal/database-keepalive/",
        views.database_keepalive,
        name="database_keepalive",
    ),
]
