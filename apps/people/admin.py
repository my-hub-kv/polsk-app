"""Emergency Admin registrations without Polsk-specific CRUD restrictions."""

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
    """Manage durable person profiles through standard Django Admin."""

    list_display = ("display_name", "age_group", "login_account")
    list_filter = ("age_group",)
    search_fields = ("display_name", "login_account__username")
    list_select_related = ("login_account",)
    autocomplete_fields = ("login_account",)


@admin.register(EventParticipation)
class EventParticipationAdmin(admin.ModelAdmin):
    """Manage event memberships through standard Django Admin."""

    list_display = ("event_year", "participant")
    list_filter = ("event_year",)
    search_fields = ("event_year__name", "participant__display_name")
    list_select_related = ("event_year", "participant")
    autocomplete_fields = ("event_year", "participant")

@admin.register(EventRoleAssignment)
class EventRoleAssignmentAdmin(admin.ModelAdmin):
    """Manage additive roles through standard Django Admin."""

    list_display = ("participation", "role")
    list_filter = ("role", "participation__event_year")
    search_fields = (
        "participation__event_year__name",
        "participation__participant__display_name",
    )
    list_select_related = ("participation__event_year", "participation__participant")
    autocomplete_fields = ("participation",)


@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    """Manage households through standard Django Admin."""

    list_display = ("name", "event_year")
    list_filter = ("event_year",)
    search_fields = ("name", "event_year__name")
    list_select_related = ("event_year",)
    autocomplete_fields = ("event_year",)

@admin.register(HouseholdMembership)
class HouseholdMembershipAdmin(admin.ModelAdmin):
    """Manage household memberships through standard Django Admin."""

    list_display = ("household", "participation")
    list_filter = ("household__event_year",)
    search_fields = (
        "household__name",
        "participation__participant__display_name",
    )
    list_select_related = (
        "household__event_year",
        "participation__event_year",
        "participation__participant",
    )
