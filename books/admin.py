from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path
from django.utils.html import format_html

from .models import Book, Narrator, Recording, QRCode, Attestation


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "public_domain", "id")
    list_filter = ("public_domain",)
    search_fields = ("title", "author")
    prepopulated_fields = {"slug": ("title",)}


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
    list_display = ("book", "narrator", "duration_seconds", "created_at")
    list_filter = ("book",)
    search_fields = ("narrator__name",)


@admin.register(QRCode)
class QRCodeAdmin(admin.ModelAdmin):
    list_display = ("book", "recording", "label_text", "password")
    list_filter = ("book",)


@admin.register(Attestation)
class AttestationAdmin(admin.ModelAdmin):
    list_display = ("narrator", "book", "attested_at")
    list_filter = ("book",)
    search_fields = ("narrator__name", "narrator__email")
