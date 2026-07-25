"""Emergency Admin registrations without Polsk-specific CRUD restrictions."""

from django.contrib import admin

from .models import Notification, NotificationDelivery, NotificationState


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Manage notifications through standard Django Admin."""

    list_display = ("created_at", "event_year", "recipient", "title", "destination_path")
    list_filter = ("event_year", "created_at")
    search_fields = ("recipient__username", "title")
    list_select_related = ("event_year", "recipient")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
@admin.register(NotificationState)
class NotificationStateAdmin(admin.ModelAdmin):
    """Manage notification read state through standard Django Admin."""

    list_display = ("event_year", "recipient", "last_opened_at")
    list_filter = ("event_year",)
    search_fields = ("recipient__username",)
    list_select_related = ("event_year", "recipient")
@admin.register(NotificationDelivery)
class NotificationDeliveryAdmin(admin.ModelAdmin):
    """Manage notification delivery records through standard Django Admin."""

    list_display = (
        "notification",
        "provider",
        "status",
        "attempts",
        "available_at",
        "claimed_at",
        "sent_at",
    )
    list_filter = ("provider", "status")
    search_fields = ("notification__recipient__username", "notification__title")
    list_select_related = ("notification__recipient",)
    ordering = ("-available_at",)
