import uuid
from django.db import models
from django.utils import timezone

from .wordlist import generate_passphrase


class EventCode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=100, unique=True)
    label = models.CharField(max_length=255, help_text="Internal label, e.g. 'October 2026 VTO Event'")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

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
    token = models.CharField(max_length=200, unique=True, default=generate_passphrase)
    label = models.CharField(max_length=255, help_text="Who this invite is for, e.g. 'Jordan - Fragforce Discord'")
    used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    narrator = models.ForeignKey(
        "books.Narrator", on_delete=models.SET_NULL, null=True, blank=True, related_name="invite_link"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

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
