from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Configure Polsk's credential and invitation application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
