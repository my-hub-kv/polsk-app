from django.contrib import admin

from .models import Notification, NotificationDelivery, NotificationState


class ReadOnlyNotificationAdmin(admin.ModelAdmin):
    """Keep Django Admin from bypassing notification service invariants."""

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(Notification, ReadOnlyNotificationAdmin)
admin.site.register(NotificationState, ReadOnlyNotificationAdmin)
admin.site.register(NotificationDelivery, ReadOnlyNotificationAdmin)
