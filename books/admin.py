from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path
from django.utils.html import format_html

from .models import Book, Narrator, Recording, QRCode, Attestation


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "public_domain", "id", "qr_sheet_link")
    list_filter = ("public_domain",)
    search_fields = ("title", "author")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("id",)

    @admin.display(description="QR Sheet")
    def qr_sheet_link(self, obj):
        url = f"/b/qr/sheet/{obj.id}/"
        return format_html('<a href="{}" target="_blank">Print</a>', url)

    def get_exclude(self, request, obj=None):
        if obj is None:
            return ("id",)
        return ()

    def get_fields(self, request, obj=None):
        if obj is None:
            fields = [f.name for f in self.model._meta.fields if f.name != "id"]
        else:
            fields = ["id"] + [f.name for f in self.model._meta.fields if f.name != "id"]
        return fields


@admin.register(Narrator)
class NarratorAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "has_passphrase", "created_at")
    search_fields = ("name", "email")
    readonly_fields = ("passphrase_display",)
    exclude = ("passphrase",)

    @admin.display(boolean=True, description="Passphrase")
    def has_passphrase(self, obj):
        return bool(obj.passphrase)

    def passphrase_display(self, obj):
        value = obj.passphrase or "(none)"
        if not obj.pk:
            return value
        return format_html(
            '{} <button type="submit" name="_generate_passphrase" class="button"'
            ' style="margin-left: 10px;">{}</button>',
            value,
            "Generate new passphrase",
        )

    passphrase_display.short_description = "Passphrase"

    def response_change(self, request, obj):
        if "_generate_passphrase" in request.POST:
            from registration.wordlist import generate_passphrase

            for _ in range(100):
                passphrase = generate_passphrase()
                if not Narrator.objects.filter(passphrase=passphrase).exists():
                    obj.passphrase = passphrase
                    obj.save(update_fields=["passphrase"])
                    self.message_user(request, f"New passphrase generated: {passphrase}")
                    return HttpResponseRedirect(request.path)
            self.message_user(request, "Failed to generate unique passphrase", level="error")
            return HttpResponseRedirect(request.path)
        return super().response_change(request, obj)


@admin.register(Recording)
class RecordingAdmin(admin.ModelAdmin):
    list_display = ("book", "narrator", "status", "duration_seconds", "flagged_for_review", "created_at")
    list_filter = ("book", "status", "flagged_for_review")
    search_fields = ("narrator__name",)
    readonly_fields = ("status",)
    actions = ["retry_failed_recordings"]

    @admin.action(description="Retry remuxing for selected failed recordings")
    def retry_failed_recordings(self, request, queryset):
        from .models import RecordingStatus
        from .processing import spawn_remux

        failed = queryset.filter(status=RecordingStatus.FAILED)
        failed_ids = list(failed.values_list("id", flat=True))
        failed.update(status=RecordingStatus.PENDING)
        for recording_id in failed_ids:
            spawn_remux(recording_id)
        self.message_user(request, f"Retrying {len(failed_ids)} recording(s).")


@admin.register(QRCode)
class QRCodeAdmin(admin.ModelAdmin):
    list_display = ("book", "recording", "short_code", "label_text", "password", "qr_links")
    list_filter = ("book",)
    readonly_fields = ("short_code",)

    @admin.display(description="QR")
    def qr_links(self, obj):
        png_url = f"/b/qr/{obj.id}.png"
        svg_url = f"/b/qr/{obj.id}.svg"
        label_url = f"/b/qr/{obj.id}/label.png"
        return format_html('<a href="{}">PNG</a> | <a href="{}">SVG</a> | <a href="{}">Label</a>', png_url, svg_url, label_url)


@admin.register(Attestation)
class AttestationAdmin(admin.ModelAdmin):
    list_display = ("narrator", "book", "attested_at")
    list_filter = ("book",)
    search_fields = ("narrator__name", "narrator__email")
