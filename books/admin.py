from django.contrib import admin
from .models import Book, Narrator, Recording, QRCode, Attestation


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "public_domain", "id")
    list_filter = ("public_domain",)
    search_fields = ("title", "author")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Narrator)
class NarratorAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "created_at")
    search_fields = ("name", "email")


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
