from django.contrib import admin

from .models import EventCode, InviteLink


@admin.register(EventCode)
class EventCodeAdmin(admin.ModelAdmin):
    list_display = ("label", "code", "active", "expires_at", "created_at")
    list_filter = ("active",)
    search_fields = ("label", "code")
    readonly_fields = ("code",)

    def get_exclude(self, request, obj=None):
        if obj is None:
            return ("code",)
        return None


@admin.register(InviteLink)
class InviteLinkAdmin(admin.ModelAdmin):
    list_display = ("label", "token", "used", "used_at", "narrator", "created_at")
    list_filter = ("used",)
    search_fields = ("label", "token")
    readonly_fields = ("token", "used", "used_at", "narrator")

    def get_exclude(self, request, obj=None):
        if obj is None:
            return ("token", "used", "used_at", "narrator")
        return None
