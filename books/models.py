import os
import secrets
import uuid

from django.conf import settings
from django.db import models

# Lowercase alphanumeric minus easily confused characters: 0/O, 1/I/l
BOOK_ID_ALPHABET = "23456789abcdefghjkmnpqrstuvwxyz"


def generate_book_id():
    return "".join(secrets.choice(BOOK_ID_ALPHABET) for _ in range(12))


class Book(models.Model):
    id = models.CharField(max_length=12, primary_key=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    author = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        if not self.id:
            for _ in range(100):
                candidate = generate_book_id()
                if not Book.objects.filter(id=candidate).exists():
                    self.id = candidate
                    break
            else:
                raise RuntimeError("Failed to generate unique book ID after 100 attempts")
        super().save(*args, **kwargs)
    illustrator = models.CharField(max_length=255, blank=True)
    publisher = models.CharField(max_length=255, blank=True)
    isbn = models.CharField(max_length=13, blank=True)
    copyright_notice = models.TextField(blank=True)
    permission_phrasing = models.TextField(blank=True)
    public_domain = models.BooleanField(default=False)
    license_expiry = models.DateField(null=True, blank=True)
    max_narrators = models.PositiveIntegerField(null=True, blank=True)
    estimated_duration = models.CharField(max_length=50, blank=True)
    full_text = models.TextField(blank=True)

    def __str__(self):
        return self.title


class Narrator(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    passphrase = models.CharField(max_length=200, unique=True, null=True, blank=True)
    registered_via_event = models.ForeignKey(
        "registration.EventCode", on_delete=models.SET_NULL, null=True, blank=True, related_name="narrators"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


def recording_upload_path(instance, filename):
    ext = filename.rsplit(".", 1)[-1] if "." in filename else "webm"
    return f"recordings/{instance.id}.{ext}"


class RecordingStatus(models.TextChoices):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class Recording(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="recordings")
    narrator = models.ForeignKey(Narrator, on_delete=models.CASCADE, related_name="recordings")
    audio_file = models.FileField(upload_to=recording_upload_path)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=12,
        choices=RecordingStatus.choices,
        default=RecordingStatus.PENDING,
        db_index=True,
    )
    flagged_for_review = models.BooleanField(default=False)
    flag_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def finalized_path(self):
        return os.path.join(settings.MEDIA_ROOT, "finalized", f"{self.id}.webm")

    @property
    def processing_path(self):
        return os.path.join(settings.MEDIA_ROOT, "processing", f"{self.id}.webm")

    @property
    def duration_formatted(self):
        if not self.duration_seconds:
            return None
        m, s = divmod(self.duration_seconds, 60)
        return f"{m}:{s:02d}"

    def __str__(self):
        return f"{self.book.title} - {self.narrator.name}"


class QRCode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="qr_codes")
    recording = models.ForeignKey(Recording, on_delete=models.SET_NULL, null=True, blank=True, related_name="qr_codes")
    password = models.CharField(max_length=10, blank=True)
    label_text = models.CharField(max_length=255)

    class Meta:
        verbose_name = "QR code"
        verbose_name_plural = "QR codes"

    def __str__(self):
        return f"QR: {self.book.title} - {self.label_text}"


class Attestation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recording = models.OneToOneField(Recording, on_delete=models.CASCADE, related_name="attestation")
    narrator = models.ForeignKey(Narrator, on_delete=models.CASCADE, related_name="attestations")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="attestations")
    attested_at = models.DateTimeField(auto_now_add=True)
    attestation_text = models.TextField()

    def __str__(self):
        return f"Attestation: {self.narrator.name} - {self.book.title}"
