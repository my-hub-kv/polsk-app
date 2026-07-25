from django.contrib import admin

from .models import EventParticipation, EventRoleAssignment, Household, HouseholdMembership, Participant

admin.site.register(Participant)
admin.site.register(EventParticipation)
admin.site.register(EventRoleAssignment)
admin.site.register(Household)


@admin.register(HouseholdMembership)
class HouseholdMembershipAdmin(admin.ModelAdmin):
    """Keep emergency admin from bypassing the event-consistent service boundary."""

    readonly_fields = ("household", "participation")

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
