from django.contrib import admin

from .models import Notification, NotificationDelivery, NotificationState


class ReadOnlyAdmin(admin.ModelAdmin):
    """Keep Django Admin from bypassing notification service invariants."""

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Notification)
class NotificationAdmin(ReadOnlyAdmin):
    """Inspect delivered in-app notices without creating new queue entries."""

    list_display = ("created_at", "event_year", "recipient", "title", "destination_path")
    list_filter = ("event_year", "created_at")
    search_fields = ("recipient__username", "title")
    list_select_related = ("event_year", "recipient")
    ordering = ("-created_at",)
    readonly_fields = (
        "public_id",
        "event_year",
        "recipient",
        "title",
        "body",
        "destination_path",
        "idempotency_key",
        "created_at",
    )


@admin.register(NotificationState)
class NotificationStateAdmin(ReadOnlyAdmin):
    """Inspect inbox read boundaries without changing participant state."""

    list_display = ("event_year", "recipient", "last_opened_at")
    list_filter = ("event_year",)
    search_fields = ("recipient__username",)
    list_select_related = ("event_year", "recipient")
    readonly_fields = ("event_year", "recipient", "last_opened_at")


@admin.register(NotificationDelivery)
class NotificationDeliveryAdmin(ReadOnlyAdmin):
    """Inspect provider-delivery progress without bypassing the dispatcher."""

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
    list_select_related = ("notification",)
    ordering = ("-available_at",)
    readonly_fields = (
        "notification",
        "provider",
        "status",
        "attempts",
        "available_at",
        "claimed_at",
        "sent_at",
        "error_code",
    )
