"""Emergency Admin registrations without Polsk-specific CRUD restrictions."""

from django.contrib import admin

from .models import Activity, EventYear


@admin.register(EventYear)
class EventYearAdmin(admin.ModelAdmin):
    """Manage the annual event boundary through standard Django Admin."""

    list_display = ("name", "year", "starts_on", "ends_on", "status", "timezone")
    list_filter = ("status", "year")
    search_fields = ("name",)
    ordering = ("-year",)
    date_hierarchy = "starts_on"


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    """Manage shared schedule records through standard Django Admin."""

    list_display = (
        "title",
        "event_year",
        "activity_date",
        "start_time",
        "end_time",
        "is_time_approximate",
        "owner_participation",
    )
    list_filter = ("event_year", "activity_date", "is_time_approximate")
    search_fields = (
        "title",
        "description",
        "owner_participation__participant__display_name",
        "created_by__username",
        "updated_by__username",
    )
    ordering = ("event_year", "activity_date", "start_time")
    date_hierarchy = "activity_date"
    list_select_related = (
        "event_year",
        "owner_participation__participant",
        "created_by",
        "updated_by",
    )
    autocomplete_fields = (
        "event_year",
        "owner_participation",
        "created_by",
        "updated_by",
    )
