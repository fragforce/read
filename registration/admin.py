from django.contrib import admin
from .models import EventCode, InviteLink


@admin.register(EventCode)
class EventCodeAdmin(admin.ModelAdmin):
    list_display = ("label", "code", "active", "expires_at", "created_at")
    list_filter = ("active",)
    search_fields = ("label", "code")


@admin.register(InviteLink)
class InviteLinkAdmin(admin.ModelAdmin):
    list_display = ("label", "token", "used", "used_at", "narrator", "created_at")
    list_filter = ("used",)
    search_fields = ("label", "token")
    readonly_fields = ("used_at", "narrator")
