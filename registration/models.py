import uuid

from django.db import models
from django.utils import timezone

from .wordlist import generate_passphrase


def generate_unique_code():
    for _ in range(100):
        code = generate_passphrase()
        if not EventCode.objects.filter(code=code).exists():
            return code
    raise RuntimeError("Failed to generate unique event code after 100 attempts")


def generate_unique_token():
    for _ in range(100):
        token = generate_passphrase()
        if not InviteLink.objects.filter(token=token).exists():
            return token
    raise RuntimeError("Failed to generate unique invite token after 100 attempts")


class EventCode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=100, unique=True)
    label = models.CharField(max_length=255, help_text="Internal label, e.g. 'October 2026 VTO Event'")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = generate_unique_code()
        super().save(*args, **kwargs)

    def is_valid(self):
        if not self.active:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True

    def __str__(self):
        return f"{self.label} ({self.code})"


class InviteLink(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(max_length=200, unique=True)
    label = models.CharField(max_length=255, help_text="Who this invite is for, e.g. 'Jordan - Fragforce Discord'")
    used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    narrator = models.ForeignKey(
        "books.Narrator", on_delete=models.SET_NULL, null=True, blank=True, related_name="invite_link"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = generate_unique_token()
        super().save(*args, **kwargs)

    def is_valid(self):
        if self.used:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True

    def mark_used(self, narrator):
        self.used = True
        self.used_at = timezone.now()
        self.narrator = narrator
        self.save()

    def __str__(self):
        status = "used" if self.used else "active"
        return f"{self.label} ({status})"
