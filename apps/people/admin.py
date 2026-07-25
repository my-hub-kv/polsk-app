from django.contrib import admin

from .models import (
    EventParticipation,
    EventRoleAssignment,
    Household,
    HouseholdMembership,
    Participant,
)


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    """Inspect durable person profiles without coupling them to login accounts."""

    list_display = ("display_name", "age_group", "login_account")
    list_filter = ("age_group",)
    search_fields = ("display_name", "login_account__username")
    list_select_related = ("login_account",)
    readonly_fields = ("public_id",)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(EventParticipation)
class EventParticipationAdmin(admin.ModelAdmin):
    """Maintain event membership with searchable event and participant context."""

    list_display = ("event_year", "participant")
    list_filter = ("event_year",)
    search_fields = ("event_year__name", "participant__display_name")
    list_select_related = ("event_year", "participant")

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(EventRoleAssignment)
class EventRoleAssignmentAdmin(admin.ModelAdmin):
    """Manage additive roles through their explicitly event-scoped participation."""

    list_display = ("participation", "role")
    list_filter = ("role", "participation__event_year")
    search_fields = (
        "participation__event_year__name",
        "participation__participant__display_name",
    )
    list_select_related = ("participation__event_year", "participation__participant")


@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    """Inspect households within their annual event boundary."""

    list_display = ("name", "event_year")
    list_filter = ("event_year",)
    search_fields = ("name", "event_year__name")
    list_select_related = ("event_year",)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(HouseholdMembership)
class HouseholdMembershipAdmin(admin.ModelAdmin):
    """Keep emergency admin from bypassing the event-consistent service boundary."""

    list_display = ("household", "participation")
    list_filter = ("household__event_year",)
    search_fields = (
        "household__name",
        "participation__participant__display_name",
    )
    list_select_related = ("household", "participation")
    readonly_fields = ("household", "participation")

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
