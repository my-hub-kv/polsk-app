"""Emergency Admin registrations without Polsk-specific CRUD restrictions."""

from django.contrib import admin

from .models import EventYear


@admin.register(EventYear)
class EventYearAdmin(admin.ModelAdmin):
    """Manage the annual event boundary through standard Django Admin."""

    list_display = ("name", "year", "starts_on", "ends_on", "status", "timezone")
    list_filter = ("status", "year")
    search_fields = ("name",)
    ordering = ("-year",)
    date_hierarchy = "starts_on"
