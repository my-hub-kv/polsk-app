from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("invitation/<str:token>/", views.redeem, name="redeem"),
    path(
        "internal/startiapp/biometric-save-completed/",
        views.startiapp_biometric_save_completed,
        name="startiapp_biometric_save_completed",
    ),
]
