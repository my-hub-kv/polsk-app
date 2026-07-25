from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Invitation, LoginThrottle, User


@admin.register(User)
class PolskUserAdmin(UserAdmin):
    """Emergency account management without exposing credential material."""

    list_display = ("username", "email", "is_active", "is_staff", "is_superuser")
    list_filter = ("is_active", "is_staff", "is_superuser")
    search_fields = ("username", "email")
    readonly_fields = ("public_id", "last_login", "date_joined")

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    """Expose invitation lifecycle without permitting raw-token reconstruction."""

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
    list_select_related = ("participation__participant",)
    exclude = ("token_digest",)
    readonly_fields = (
        "participation",
        "purpose",
        "expires_at",
        "used_at",
        "revoked_at",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(LoginThrottle)
class LoginThrottleAdmin(admin.ModelAdmin):
    """Inspect short-lived login protection without exposing the source values."""

    list_display = ("failures", "window_started_at", "locked_until", "updated_at")
    list_filter = ("locked_until",)
    ordering = ("-updated_at",)
    exclude = ("key_digest",)
    readonly_fields = (
        "window_started_at",
        "failures",
        "locked_until",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
