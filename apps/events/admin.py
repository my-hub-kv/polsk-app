from django.contrib import admin

from .models import EventYear


@admin.register(EventYear)
class EventYearAdmin(admin.ModelAdmin):
    """Manage the annual event boundary from the unlinked emergency backend."""

    list_display = ("name", "year", "starts_on", "ends_on", "status", "timezone")
    list_filter = ("status", "year")
    search_fields = ("name",)
    ordering = ("-year",)
    readonly_fields = ("public_id",)

    def has_delete_permission(self, request, obj=None):
        return False
