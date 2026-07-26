from django.urls import path

from apps.accounts.forms import PolskAuthenticationForm
from apps.accounts.views import PolskLogoutView, RateLimitedLoginView

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path(
        "login/",
        RateLimitedLoginView.as_view(
            template_name="registration/login.html",
            authentication_form=PolskAuthenticationForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path(
        "logout/",
        PolskLogoutView.as_view(template_name="core/logged_out.html"),
        name="logout",
    ),
    path("opgaver/", views.chores, name="chores"),
    path("beskeder/", views.messages, name="messages"),
    path("mad-og-indkoeb/", views.food_and_shopping, name="food_and_shopping"),
    path("mere/", views.more, name="more"),
    path("administration/", views.administration, name="administration"),
    path(
        "administration/behandl-notifikationer/",
        views.process_notifications,
        name="process_notifications",
    ),
    path(
        "administration/ryd-loginbeskyttelse/",
        views.cleanup_login_protection,
        name="cleanup_login_protection",
    ),
    path("aktiviteter/", views.activities, name="activities"),
    path(
        "aktiviteter/<uuid:activity_public_id>/",
        views.activity_detail,
        name="activity_detail",
    ),
    path("deltagere/", views.directory, name="directory"),
    path(
        "deltagere/<uuid:participant_public_id>/nulstil-adgang/",
        views.reset_credentials,
        name="reset_credentials",
    ),
    path("notifikationer/", views.notifications, name="notifications"),
    path(
        "notifikationer/åbnet/",
        views.mark_notifications_opened,
        name="mark_notifications_opened",
    ),
    path("profil/", views.profile, name="profile"),
    path("profil/skift/", views.switch_profile, name="switch_profile"),
    path("tidligere-aar/", views.history, name="history"),
    path("vejr/", views.weather, name="weather"),
    path("mad/", views.food, name="food"),
    path("indkoeb/", views.shopping, name="shopping"),
    path("health/", views.health, name="health"),
    path("internal/client-errors/", views.client_error, name="client_error"),
    path(
        "internal/database-keepalive/",
        views.database_keepalive,
        name="database_keepalive",
    ),
]
