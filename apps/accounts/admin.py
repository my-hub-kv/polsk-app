"""Emergency Admin registrations without Polsk-specific CRUD restrictions."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Invitation, InvitationThrottle, LoginThrottle, User


@admin.register(User)
class PolskUserAdmin(UserAdmin):
    """Use Django's standard account administration for emergency repair."""

    list_display = ("username", "email", "is_active", "is_staff", "is_superuser")
    list_filter = ("is_active", "is_staff", "is_superuser")
    search_fields = ("username", "email")


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    """Use Django's standard invitation administration for emergency repair."""

    list_display = (
        "participation",
        "purpose",
        "expires_at",
        "used_at",
        "revoked_at",
        "created_at",
    )
    list_filter = ("purpose", "used_at", "revoked_at")
    search_fields = (
        "participation__participant__display_name",
        "participation__participant__login_account__username",
    )
    list_select_related = ("participation__event_year", "participation__participant")


@admin.register(LoginThrottle)
class LoginThrottleAdmin(admin.ModelAdmin):
    """Use Django's standard throttle administration for emergency repair."""

    list_display = ("failures", "window_started_at", "locked_until", "updated_at")
    list_filter = ("locked_until",)
    ordering = ("-updated_at",)


@admin.register(InvitationThrottle)
class InvitationThrottleAdmin(LoginThrottleAdmin):
    """Inspect short-lived invitation protection without exposing source values."""
