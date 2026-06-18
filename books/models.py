import uuid
from django.db import models


class Book(models.Model):
    id = models.CharField(max_length=12, primary_key=True)
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
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
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Recording(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="recordings")
    narrator = models.ForeignKey(Narrator, on_delete=models.CASCADE, related_name="recordings")
    audio_file = models.FileField(upload_to="recordings/")
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

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
