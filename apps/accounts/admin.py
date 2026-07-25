from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Invitation, LoginThrottle, User


@admin.register(User)
class PolskUserAdmin(UserAdmin):
    readonly_fields = ("public_id",)


admin.site.register(Invitation)
admin.site.register(LoginThrottle)
